import streamlit as st
from openai import OpenAI
import json
import os
import plotly.graph_objects as go
from dotenv import load_dotenv
import datetime
import copy

load_dotenv()

# ----------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------
st.set_page_config(
    page_title="Cultural Preservation Simulation",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0f1117; color: #e8e8e8; }
    .chapter-header {
        font-size: 2rem; font-weight: 700; color: #ffffff;
        border-left: 5px solid #7F77DD; padding-left: 16px;
        margin-bottom: 8px;
    }
    .chapter-sub {
        font-size: 1rem; color: #9999bb; margin-bottom: 24px;
        padding-left: 21px;
    }
    .narrative-box {
        background: #1a1a2e; border-left: 4px solid #534AB7;
        border-radius: 8px; padding: 20px 24px;
        color: #d4d4f0; font-size: 0.97rem; line-height: 1.8;
        margin: 16px 0;
    }
    .geo-box {
        background: #0d2b1a; border-left: 4px solid #1D9E75;
        border-radius: 8px; padding: 16px 20px;
        color: #9fe1cb; font-size: 0.9rem; line-height: 1.7;
        margin: 12px 0;
    }
    .mr-score-box { border-radius: 12px; padding: 24px; text-align: center; margin: 16px 0; }
    .mr-good { background: #0d2b0d; border: 2px solid #1D9E75; }
    .mr-warn { background: #2b1f0d; border: 2px solid #EF9F27; }
    .mr-crit { background: #2b0d0d; border: 2px solid #E24B4A; }
    .mr-num  { font-size: 3.5rem; font-weight: 800; }
    .mr-label { font-size: 0.9rem; color: #aaaaaa; margin-top: 4px; }
    .driver-tag {
        background: #2a2040; border-radius: 6px;
        padding: 8px 14px; color: #AFA9EC;
        font-size: 0.88rem; display: block; margin-bottom: 8px;
    }
    .stage-badge {
        background: #534AB7; color: white; border-radius: 20px;
        padding: 4px 14px; font-size: 0.8rem; font-weight: 600;
        display: inline-block; margin-bottom: 12px;
    }
    .provider-badge {
        border-radius: 20px; padding: 3px 12px;
        font-size: 0.75rem; font-weight: 600;
        display: inline-block; margin-left: 8px;
    }
    .groq-badge  { background: #0d2b1a; color: #5DCAA5; border: 1px solid #1D9E75; }
    .openai-badge { background: #1a1a2e; color: #AFA9EC; border: 1px solid #534AB7; }
    .stButton > button {
        background: #534AB7; color: white; border: none;
        border-radius: 8px; padding: 10px 24px; font-weight: 600;
    }
    .stButton > button:hover { background: #7F77DD; }
    div[data-testid="stSidebar"] { background: #0d0d1a; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------
# LLM CALLER (OpenAI primary, Groq fallback)
# ----------------------------------------------------------------
GROQ_KEY   = os.getenv("GROQ_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

def call_llm(prompt: str, json_mode: bool = True) -> tuple[str, str]:
    providers = []
    if OPENAI_KEY:
        providers.append(("OpenAI", OpenAI(api_key=OPENAI_KEY), "gpt-4o-mini"))
    if GROQ_KEY:
        providers.append(("Groq", OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_KEY
        ), "llama-3.3-70b-versatile"))
    if not providers:
        return "ERROR: No API keys found. Add OPENAI_API_KEY or GROQ_API_KEY to .env", ""
    last_error = ""
    for provider_name, client, model in providers:
        try:
            kwargs = dict(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2048,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content, provider_name
        except Exception as e:
            last_error = f"{provider_name} error: {str(e)}"
            continue
    return f"ERROR: All providers failed. Last error: {last_error}", ""

def parse_json(text: str) -> dict:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass
    return {}

def compute_mr(scores: dict) -> float:
    a = scores.get("language", 50)
    b = scores.get("cultural_practice", 50)
    c = (scores.get("social_affiliation", 50) + scores.get("self_presentation", 50)) / 2
    return round((a + b + c) / 3, 1)

def mr_class(mr): return "mr-good" if mr >= 65 else ("mr-warn" if mr >= 40 else "mr-crit")
def mr_label(mr): return "Strong preservation" if mr >= 65 else ("Moderate erosion" if mr >= 40 else "Critical erosion")
def mr_color(mr): return "#1D9E75" if mr >= 65 else ("#EF9F27" if mr >= 40 else "#E24B4A")
def provider_badge(provider: str) -> str:
    cls = "openai-badge" if provider == "OpenAI" else "groq-badge"
    return f'<span class="provider-badge {cls}">via {provider}</span>'

# ----------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------
def init_state():
    defaults = {
        "stage": "setup", "json_state": {}, "trajectory": [],
        "narratives": [], "pivot_choice": None,
        "geo_context": "", "cfg": {}, "providers_used": [],
        "state_snapshots": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

def record_snapshot(name: str):
    snapshot = {
        "timestamp": datetime.datetime.now().isoformat(),
        "stage": st.session_state.stage,
        "snapshot_name": name,
        "json_state": copy.deepcopy(st.session_state.json_state)
    }
    st.session_state.state_snapshots.append(snapshot)

# ----------------------------------------------------------------
# CHART
# ----------------------------------------------------------------
def build_chart(trajectory: list) -> go.Figure:
    stages = [t["stage"] for t in trajectory]
    fig = go.Figure()
    series = [
        ("language",          "Language",           "#7F77DD"),
        ("cultural_practice", "Cultural practice",  "#1D9E75"),
        ("social_affiliation","Social affiliation",  "#EF9F27"),
        ("self_presentation",  "Self-presentation",  "#D85A30"),
    ]
    for key, name, color in series:
        fig.add_trace(go.Scatter(
            x=stages, y=[t["scores"].get(key, 0) for t in trajectory],
            mode="lines+markers", name=name, line=dict(color=color, width=2.5)
        ))
    fig.add_trace(go.Scatter(
        x=stages, y=[compute_mr(t["scores"]) for t in trajectory],
        mode="lines+markers", name="MR composite",
        line=dict(color="#000000", width=3, dash="dash")
    ))
    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#111111", family="Inter, sans-serif", size=12),
        legend=dict(bgcolor="#FFFFFF", bordercolor="#CCCCCC", borderwidth=1, font=dict(color="#111111", size=11)),
        xaxis=dict(gridcolor="#E0E0E0", title="Life stage", title_font=dict(color="#111111", size=13), tickfont=dict(color="#111111", size=11)),
        yaxis=dict(gridcolor="#E0E0E0", title="Score (0–100)", range=[0,100], title_font=dict(color="#111111", size=13), tickfont=dict(color="#111111", size=11)),
        margin=dict(l=40, r=20, t=20, b=40),
        height=340
    )
    return fig

# ----------------------------------------------------------------
# PROMPTS
# ----------------------------------------------------------------
def geo_research_prompt(cfg: dict) -> str:
    return f"""You are a cultural sociologist specializing in diaspora studies and immigrant assimilation research.

Migration context:
- Origin: {cfg['origin_city']}, {cfg['origin_country']}
- Destination: {cfg['dest_city']}, {cfg['dest_country']}
- Heritage language: {cfg['language']}

Produce a structured analytical summary covering ALL of the following. Be specific — name real places, organizations, and documented patterns where you know them. Acknowledge uncertainty honestly.

1. DIASPORA PRESENCE: Approximate size and concentration of the {cfg['origin_country']} community in {cfg['dest_city']}. Name specific neighborhoods, cultural corridors, or enclaves if they exist.

2. INSTITUTIONAL INFRASTRUCTURE: Known cultural institutions serving this group (places of worship, cultural associations, language schools, community centers, restaurants, annual events). Name at least one specific institution if you know it.

3. CULTURAL DISTANCE ASSESSMENT: How different are {cfg['origin_country']} and {cfg['dest_country']} on key sociological dimensions? Consider: individualism vs collectivism, religious environment, family structure norms, language distance, and attitudes toward ethnic identity. Rate the overall cultural distance as Low, Moderate, or High and explain why in one sentence.

4. ASSIMILATION PRESSURE: Based on the destination city's demographics, economic structure, and social norms — how strong is the pressure to assimilate quickly? Is this a city where maintaining a distinct cultural identity is relatively accepted, or one where blending in is the dominant expectation?

5. HOST CULTURE RECEPTION: How does {cfg['dest_city']} generally receive immigrants from {cfg['origin_country']}? Are there documented patterns of warm reception, social friction, discrimination, or strong community solidarity?

Write this as 6-8 sentences of plain analytical prose. No JSON. No bullet points. No headers. Do not use the words "vibrant" or "rich culture."
"""

def geo_structured_prompt(cfg: dict) -> str:
    return f"""You are a cultural sociologist specializing in diaspora studies. Research the {cfg['origin_country']} community in {cfg['dest_city']}, {cfg['dest_country']}.

Now research for:
- Origin: {cfg['origin_city']}, {cfg['origin_country']}
- Destination: {cfg['dest_city']}, {cfg['dest_country']}
- Heritage language: {cfg['language']}

Be specific. Name real places if you have reliable knowledge. If uncertain, set to null. Do NOT make up any names.

Return ONLY valid JSON with the following structure. If you don't know a specific item, use null or an empty string/array. Do not invent false information.

{{
  "diaspora_presence": {{
    "population_estimate": "brief estimate (e.g., '5,000-10,000') or 'unknown'",
    "neighborhoods": ["specific neighborhood names where the community lives", "or empty list"],
    "notes": "one sentence about concentration or growth"
  }},
  "institutions": {{
    "restaurants": ["name of real restaurant", "or empty list"],
    "places_of_worship": ["church, mosque, temple with cultural services", "or empty list"],
    "cultural_centers": ["community center, cultural association", "or empty list"],
    "language_schools": ["heritage language classes", "or empty list"],
    "annual_events": ["festivals, parades, celebrations", "or empty list"]
  }},
  "schools_and_universities": {{
    "k12_schools_with_diversity": ["schools known for diverse student body or ESL programs", "or empty list"],
    "universities_with_cultural_groups": ["colleges with active cultural clubs or diaspora associations", "or empty list"]
  }},
  "similarities_to_origin": {{
    "architecture": "any resemblance in building styles, housing, or landmarks (e.g., 'some Spanish colonial influences') or 'none notable'",
    "geography": "landscape features similar to origin (e.g., 'coastal, beaches, mountains, rivers') or 'different'",
    "climate": "comparison (e.g., 'similar warm summers but colder winters')",
    "public_spaces": "parks, plazas, markets that might feel familiar (e.g., 'central market similar to home') or 'none'"
  }},
  "assimilation_pressure": "one sentence on how strong the pressure is to adopt host culture (Low/Moderate/High) and why",
  "reception": "one sentence on how the host community generally receives immigrants from this origin"
}}
"""

def profile_agent_prompt(cfg: dict, geo_context: str) -> str:
    bio = cfg.get("biography", "").strip()
    if bio:
        bio_block = f"""
PERSONAL CULTURAL ANCHOR (user-provided):
\"{bio}\"
Extract the single most specific detail from this (a dish name, a sound, a person, a weekly routine). Use that exact detail in the narrative. Do not replace it with a generic version.
"""
    else:
        bio_block = "No personal anchor provided. Do not invent one. Simply write the narrative without referencing any specific dish, ritual, or memory."

    return f"""You are the Profile Agent in a cultural preservation simulation. Persona: "The Architect."
Translate sociological variables into a culturally grounded baseline, informed by real geographic and sociological context.

BANNED WORDS — never use: vibrant, vibrant community, beloved, rich culture, cultural tapestry, strong sense of belonging, cultural scene, bustling.
Write as a specific observer of one person's particular life. Not a travel writer.

{bio_block}

GEOGRAPHIC AND SOCIOLOGICAL CONTEXT:
{geo_context}

User configuration:
- Origin: {cfg['origin_city']}, {cfg['origin_country']}
- Destination: {cfg['dest_city']}, {cfg['dest_country']}
- Heritage language: {cfg['language']}
- Age at migration: {cfg['age']}
- Cultural anchor (1-10): {cfg['anchor']}
- Heritage language use at home (1-10): {cfg['language_use']}
- Social homophily (1-10): {cfg['homophily']}
- Neighborhood cultural density: {cfg['density']}
- Institutional anchor present: {cfg['institutional']}
- Intergenerational transmission pressure (1-10): {cfg['transmission']}

Use cultural distance from the geographic context to calibrate scores.
High cultural distance between origin and destination lowers starting social affiliation scores.
Write a 4-5 sentence narrative in second person. Name the destination city. Reference the specific personal anchor detail if one was provided.

Return ONLY valid JSON:
{{
  "scores": {{
    "language": <int 0-100>,
    "cultural_practice": <int 0-100>,
    "social_affiliation": <int 0-100>,
    "self_presentation": <int 0-100>
  }},
  "resilience_anchors": ["<dimension: reason>", "<dimension: reason>"],
  "risk_factors": ["<dimension: reason>", "<dimension: reason>"],
  "community_density_assessment": "<one sentence on geographic and cultural distance support level>",
  "personal_anchor_used": "<the specific detail extracted or invented>",
  "narrative": "<4-5 sentence second-person narrative — specific events, no banned words>"
}}"""

def drift_agent_prompt(state: dict, stage_name: str, stage_ages: str, cfg: dict, pivot: str = None) -> str:
    bio = cfg.get("biography", "").strip()
    personal_anchor = state.get("personal_anchor_used", "") or bio
    anchor_note = f"Personal anchor — reference if relevant to this stage: {personal_anchor}" if personal_anchor else ""
    pivot_ctx = f"\nCRITICAL: At age 18 this person chose: '{pivot}'. This must produce a real named change in at least one dimension — describe the specific consequence in the narrative." if pivot else ""

    return f"""You are the Drift Simulation Agent. Persona: "The Simulator."
Model compounding cultural pressure across life stages with sociological accuracy.

BANNED WORDS — never use: vibrant, vibrant community, beloved, rich culture, cultural tapestry, strong sense of belonging, cultural scene, bustling.
Write about specific events, specific friction, specific moments. Not atmosphere.

PERSONALISATION RULE:
CRITICAL INSTRUCTION – NARRATIVE MUST INCLUDE USER'S CHOICES:
- You MUST begin the narrative by explicitly naming the choice(s) the user made in the PREVIOUS stage (if any). Use the exact label(s) from the USER'S RECENT CHOICE field above.
- If multiple choices were made, mention each one and describe how they felt together (e.g., "You joined the Cultural Youth Group but also practiced softening your accent – two pulls in opposite directions.")
- Write in second person ("You...") throughout.
- Never write a narrative that could apply to any user. Every narrative must reference the specific city, the specific heritage language, and the specific choices from the previous stage.

Example: "After your decision to join the Cultural Youth Group last year, you started meeting other Nigerian teens on Sundays. But at the same time, you kept filtering your accent – a tug‑of‑war between belonging and blending."

Geographic context: {cfg['origin_city']}, {cfg['origin_country']} → {cfg['dest_city']}, {cfg['dest_country']}
Heritage language: {cfg['language']}

Current JSON state:
{json.dumps(state, indent=2)}

Life stage: {stage_name} ({stage_ages})
{pivot_ctx}

VOLATILITY RULES:
- Scores compound from prior stage. Never reset.
- Do NOT produce smooth uniform changes. Real identity drift is uneven.
- Sharp drops (15+ points): describe a specific triggering event — being mocked for an accent, a parent conflict over traditional clothing, a moment of code-switching that felt wrong. Name the event.
- Score rises (Re-awakening): describe the specific trigger — a cousin visiting, finding a specific restaurant, a conversation that recalled something particular.
- Stagnation is valid. Some stages barely change a dimension. Model this when appropriate.
- If institutional anchors are present in Early Adulthood, Re-awakening is possible.
- Identify the single most influential sociological variable this stage.
- Flag tipping points: any dimension dropping more than 15 points.
- Write 4-5 sentences in second person. Name the city. Specific events only.

IMPORTANT – FAILURE LOG RULE:
- Compare each score in "scores" with the SAME score in the "Current JSON state" at the top of this prompt.
- If the absolute drop (old - new) is >15 for language, cultural_practice, social_affiliation, OR self_presentation, set "failure_log" to a one‑sentence description of the event that caused that drop.
- If the drop is ≤15 for all four dimensions, set "failure_log" to an empty string ("").
- Do NOT log drops of 15 or less. Do NOT invent drops that did not happen.

Return ONLY valid JSON:
{{
  "scores": {{
    "language": <int 0-100>,
    "cultural_practice": <int 0-100>,
    "social_affiliation": <int 0-100>,
    "self_presentation": <int 0-100>
  }},
  "primary_driver": "<variable and one specific explanation>",
  "narrative": "<4-5 sentence second-person narrative — specific events, no banned words>",
  "failure_log": "<empty string, or description of the specific tipping point event>"
}}"""

def reflection_agent_prompt(state: dict, trajectory: list, cfg: dict, geo_context: str) -> str:
    escalation = ""
    if state.get("tipping_point_occurred"):
        escalation = """
CRITICAL: A tipping point (score drop >15 points in one stage) occurred during the simulation.
- In your "ranked_drivers", the event from that stage MUST be listed as #1.
- In your "turning_point", describe that specific drop as the dominant shift.
- Do not ignore this instruction.
"""
    return f"""You are the Reflection Agent. Persona: "The Analyst."
Produce rigorous, evidence-based synthesis. No generic summaries.

Geographic context: {cfg['origin_city']}, {cfg['origin_country']} → {cfg['dest_city']}, {cfg['dest_country']}
Heritage language: {cfg['language']}
Community context: {geo_context}

Full trajectory:
{json.dumps(trajectory, indent=2)}

Final state:
{json.dumps(state, indent=2)}

{escalation}

Be specific. Name the city. Reference diaspora community context. Connect to real patterns.

Return ONLY valid JSON:
{{
  "narrative_summary": "<4-5 sentence second-person arc summary>",
  "turning_point": "<specific stage, what shifted, and why>",
  "ranked_drivers": [
    "<1. variable: one sentence>",
    "<2. variable: one sentence>",
    "<3. variable: one sentence>"
  ],
  "counterfactual_a": "<What if destination had opposite diaspora density? Name a real alternative city. Estimate score difference.>",
  "counterfactual_b": "<What if the person chose a different pivot? Name the alternative and estimate impact.>",
  "preservation_verdict": "<One sentence: Strong Preservation / Moderate Erosion / Critical Erosion and why>",
  "research_note": "<One sentence connecting to broader migration literature>"
}}"""

def quick_geo_validation(cfg: dict) -> tuple[bool, str]:
    prompt = f"""You are a geography validator. Check if this migration route is geographically plausible and not obviously swapped or fictional.

- Origin: {cfg['origin_city']}, {cfg['origin_country']}
- Destination: {cfg['dest_city']}, {cfg['dest_country']}

A pair is implausible if:
- The city does not exist in the stated country (e.g., "New York, Nigeria")
- The user swapped origin and destination (e.g., origin = "Lagos, USA", destination = "New York, Nigeria")
- Either city is completely fictional
- The heritage language does not exist or is not widely spoken in the origin country (e.g., 'Spanish' in Nigeria is highly suspicious, Igbo in Puerto Rico).

Return ONLY a JSON object with:
{{"plausible": true/false, "reason": "one-sentence explanation"}}

Do not add any extra text.
"""
    response, _ = call_llm(prompt, json_mode=True)
    try:
        data = json.loads(response)
        return data.get("plausible", True), data.get("reason", "No reason provided")
    except:
        return True, "Validation skipped due to parsing error."

# ----------------------------------------------------------------
# DRIFT HELPER (snapshots only at handoffs, no per‑choice snapshots)
# ----------------------------------------------------------------
def run_drift_stage(stage_key, stage_name, stage_ages, badge, title, sub,
                    next_stage, next_label, stage_choices=None):
    render_progress()
    st.markdown(f'<div class="stage-badge">{badge}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chapter-header">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chapter-sub">{sub}</div>', unsafe_allow_html=True)

    cache_key = f"drift_result_{stage_key}"
    if cache_key not in st.session_state:
        pending_choice = st.session_state.get(f"pending_choice_{stage_key}", None)
        extra_context = ""
        if pending_choice:
            extra_context = f"\nUSER'S RECENT CHOICE: {pending_choice['choice']}\nYour narrative MUST mention these specific choices by name at the beginning.\n"
            del st.session_state[f"pending_choice_{stage_key}"]

        with st.spinner(f"Drift Agent simulating {stage_name}..."):
            prompt = drift_agent_prompt(
                st.session_state.json_state, stage_name, stage_ages,
                st.session_state.cfg, pivot=None
            ) + extra_context
            raw, provider = call_llm(prompt, json_mode=True)
            result = parse_json(raw)

        if not result or "scores" not in result:
            st.error(f"Drift Agent failed. Response: {raw[:600]}")
            st.stop()

        old_scores = st.session_state.json_state.get("scores", {})
        failure_detected = False
        for dim in ["language", "cultural_practice", "social_affiliation", "self_presentation"]:
            old = old_scores.get(dim, 50)
            new = result["scores"].get(dim, 50)
            if old - new > 15:
                failure_detected = True
                if not result.get("failure_log"):
                    result["failure_log"] = f"Automatic: {dim} dropped {old - new:.0f} points."

        if failure_detected:
            st.warning(f"⚠️ Cultural tipping point detected: {result['failure_log']}. The simulation is entering a less‑predictable zone.")
            st.session_state.json_state["tipping_point_occurred"] = True

        st.session_state[cache_key] = result
        st.session_state[f"provider_{stage_key}"] = provider
        st.session_state.json_state["scores"] = result["scores"]
        st.session_state.json_state["stage_history"].append({"stage": stage_name, **result})
        if result.get("failure_log"):
            st.session_state.json_state["failure_log"].append(
                {"stage": stage_name, "event": result["failure_log"]}
            )
        st.session_state.trajectory.append({"stage": stage_name, "scores": result["scores"]})
        st.session_state.narratives.append(result.get("narrative", ""))
        # Snapshot after Drift Agent LLM (before any user choices)
        record_snapshot(f"after_drift_{stage_name}")

    result = st.session_state[cache_key]
    provider = st.session_state.get(f"provider_{stage_key}", "")
    st.markdown(
        f'<div class="narrative-box">{result.get("narrative", "")}{provider_badge(provider)}</div>',
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="driver-tag">Primary driver: {result.get("primary_driver", "")}</div>', unsafe_allow_html=True)
    if result.get("failure_log"):
        st.warning(f"Tipping point detected: {result['failure_log']}")

    mr = compute_mr(result["scores"])
    st.markdown(f'<div class="mr-score-box {mr_class(mr)}"><div class="mr-num" style="color:{mr_color(mr)}">{mr}</div><div class="mr-label">MR after {stage_name} — {mr_label(mr)}</div></div>', unsafe_allow_html=True)
    st.plotly_chart(build_chart(st.session_state.trajectory), use_container_width=True)

    if stage_choices:
        st.markdown("### Select all that apply to your experience (max 3)")
        choice_key = f"selected_{stage_key}"
        baseline_key = f"baseline_{stage_key}"

        if baseline_key not in st.session_state:
            st.session_state[baseline_key] = st.session_state.json_state["scores"].copy()
        if choice_key not in st.session_state:
            st.session_state[choice_key] = []

        current = st.session_state[choice_key]
        max_reached = len(current) >= 3

        def compute_total_deltas(selected):
            total = {"language": 0, "cultural_practice": 0, "social_affiliation": 0, "self_presentation": 0}
            n = len(selected)
            scale = 1.0 if n == 1 else 0.7 if n == 2 else 0.5 if n == 3 else 0
            for label in selected:
                for ch in stage_choices:
                    if ch['label'] == label and 'score_deltas' in ch:
                        for dim, delta in ch['score_deltas'].items():
                            total[dim] += int(delta * scale)
            return total

        def apply_total():
            deltas = compute_total_deltas(current)
            base = st.session_state[baseline_key]
            new_scores = {}
            for dim in ["language", "cultural_practice", "social_affiliation", "self_presentation"]:
                new_val = base.get(dim, 50) + deltas.get(dim, 0)
                new_scores[dim] = max(0, min(100, new_val))
            st.session_state.json_state["scores"] = new_scores
            st.session_state.trajectory[-1]["scores"] = new_scores.copy()
            # NO snapshot here – this is on every checkbox toggle

        cols = st.columns(3)
        for i, choice in enumerate(stage_choices):
            with cols[i % 3]:
                is_checked = choice['label'] in current
                disabled = max_reached and not is_checked
                changed = st.checkbox(
                    f"**{choice['label']}**",
                    value=is_checked,
                    key=f"chk_{stage_key}_{i}",
                    help=choice['description'],
                    disabled=disabled
                )
                if changed != is_checked:
                    if changed and len(current) >= 3:
                        st.toast("Maximum 3 selections. Uncheck one first.", icon="⚠️")
                    else:
                        if changed:
                            current.append(choice['label'])
                        else:
                            current.remove(choice['label'])
                        apply_total()
                        st.rerun()

        if current:
            st.markdown(f"**Your choices:** {', '.join(current)}")
        else:
            st.info("Select at least one option to continue.")

        # Critical erosion check (MR < 20)
        current_mr = compute_mr(st.session_state.json_state["scores"])
        critical_handled = st.session_state.get(f"critical_handled_{stage_key}", False)

        if current_mr < 20 and not critical_handled:
            st.error(f"⚠️ CRITICAL EROSION: Your cultural preservation score has dropped to {current_mr}. Your identity is at severe risk.")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Continue anyway (accept the loss)"):
                    st.session_state[f"critical_handled_{stage_key}"] = True
                    st.rerun()
            with col2:
                if st.button("Go back and choose differently"):
                    st.session_state[choice_key] = []
                    st.session_state.json_state["scores"] = st.session_state[baseline_key].copy()
                    st.session_state.trajectory[-1]["scores"] = st.session_state[baseline_key].copy()
                    st.session_state[f"critical_handled_{stage_key}"] = False
                    st.rerun()
            with col3:
                if st.button("End simulation and view partial report"):
                    st.session_state.stage = "reflection"
                    st.rerun()
            st.stop()

        # Normal Continue button – snapshot after finalizing choices
        if st.button(f"{next_label} →", key=f"btn_{stage_key}", disabled=len(current) == 0):
            record_snapshot(f"after_choices_{stage_name}")
            st.session_state.json_state["stage_history"][-1]["user_choices"] = current.copy()
            st.session_state.trajectory[-1]["choices"] = current.copy()
            st.session_state[f"pending_choice_{next_stage}"] = {
                "choice": ", ".join(current),
                "intent": f"User selected {len(current)} actions"
            }
            del st.session_state[choice_key]
            del st.session_state[baseline_key]
            st.session_state.pop(f"critical_handled_{stage_key}", None)
            st.session_state.stage = next_stage
            st.rerun()
    else:
        # No choices – snapshot already taken after drift LLM, no extra snapshot
        if st.button(f"{next_label} →", key=f"btn_{stage_key}"):
            st.session_state.stage = next_stage
            st.rerun()

# ----------------------------------------------------------------
# STAGE-SPECIFIC CHOICE SETS (your existing lists)
# ----------------------------------------------------------------
choices_adolescence = [
    {"label": "The 'Stinky Lunch' Moment", "description": "You stop bringing traditional food to school after a classmate makes a face. You insist on 'normal' sandwiches from now on.", "impact_hint": "Cultural practice drops sharply; self‑presentation shifts toward host norms.", "score_deltas": {"cultural_practice": -10, "self_presentation": 8}},
    {"label": "The Accent Filter", "description": "You spend hours in front of the mirror softening your vowels to sound more 'local' and avoid being asked 'where are you really from?'", "impact_hint": "Language score falls; self‑presentation increases (assimilation).", "score_deltas": {"language": -8, "self_presentation": 12}},
    {"label": "The Saturday School Sentence", "description": "Your parents force you into weekend heritage language classes. You go, but you resent losing your Saturdays.", "impact_hint": "Language improves, but social affiliation with local peers suffers.", "score_deltas": {"language": 10, "social_affiliation": -5}},
    {"label": "Cultural Youth Group", "description": "You join a heritage youth wing (e.g., a Nigerian Youth Association or church group). You find friends who 'get it'.", "impact_hint": "Social affiliation and cultural practice rise together.", "score_deltas": {"social_affiliation": 12, "cultural_practice": 6}},
    {"label": "Digital Diaspora", "description": "You spend your time on TikTok/YouTube consuming media from your origin country instead of local trends.", "impact_hint": "Cultural practice and language improve without leaving your room.", "score_deltas": {"cultural_practice": 8, "language": 5}},
    {"label": "The 'Interpreter' Burden", "description": "You are the primary translator for your parents at the doctor and the bank. You feel older than your peers.", "impact_hint": "Language skills stay sharp, but you feel the weight of responsibility.", "score_deltas": {"language": 10, "self_presentation": -5}},
    {"label": "Refusing Traditional Dress", "description": "You refuse to wear traditional attire to a family wedding, opting for a Western suit/dress to look like people on social media.", "impact_hint": "Cultural practice drops, but you feel more 'normal' among friends.", "score_deltas": {"cultural_practice": -8, "self_presentation": 8}},
    {"label": "Secret Social Life", "description": "You maintain two personas—one for home and one for friends—to avoid parental pressure.", "impact_hint": "Social affiliation with peers improves, but internal identity conflict grows.", "score_deltas": {"social_affiliation": 8, "self_presentation": -10}}
]

choices_early_adulthood = [
    {"label": "The Resume Name‑Change", "description": "You realize your name is being skipped for interviews. You adopt a 'Western' first name on your CV and LinkedIn.", "impact_hint": "Professional self‑presentation improves; social affiliation with co‑ethnics may drop.", "score_deltas": {"self_presentation": 15, "social_affiliation": -6}},
    {"label": "Founding a Campus Org", "description": "There's no club for your culture on campus, so you start one. You become a 'cultural hub'.", "impact_hint": "Social affiliation and cultural practice surge.", "score_deltas": {"social_affiliation": 18, "cultural_practice": 12}},
    {"label": "The 'Intro to [Origin]' Class", "description": "You take an academic course on your own culture to learn the history you missed in high school.", "impact_hint": "Cultural practice and language get an intellectual boost.", "score_deltas": {"cultural_practice": 10, "language": 6}},
    {"label": "Dating Preference", "description": "You consciously filter your dating apps to only show people of your same heritage for 'long‑term compatibility'.", "impact_hint": "Social affiliation with co‑ethnics strengthens.", "score_deltas": {"social_affiliation": 12, "cultural_practice": 4}},
    {"label": "Professional Code‑Switching", "description": "You adopt a 'Professional Voice' at your internship, completely stripping your heritage influence during work hours.", "impact_hint": "Self‑presentation rises, but heritage language use declines.", "score_deltas": {"self_presentation": 12, "language": -8}},
    {"label": "The Kitchen Anchor", "description": "Away from home, you realize you don't know how to cook. You call your mother weekly to learn family recipes.", "impact_hint": "Cultural practice and social affiliation improve through family connection.", "score_deltas": {"cultural_practice": 10, "social_affiliation": 5}},
    {"label": "Social Relocation", "description": "You choose your first post‑grad job based on which city has the largest diaspora neighborhood.", "impact_hint": "You effectively increase your neighborhood density and social affiliation.", "score_deltas": {"social_affiliation": 12, "cultural_practice": 6}},
    {"label": "Heritage Travel", "description": "You use your first savings to travel back to your origin country without your parents, seeing it through 'adult eyes'.", "impact_hint": "Reconnection boosts language, practice, and social identity.", "score_deltas": {"language": 8, "cultural_practice": 12, "social_affiliation": 8}}
]

choices_established_life = [
    {"label": "The Naming Legacy", "description": "You decide that if you have children, they will have traditional names, no matter how 'hard to pronounce'.", "impact_hint": "Cultural practice and intergenerational transmission rise.", "score_deltas": {"cultural_practice": 12, "self_presentation": 4}},
    {"label": "Enclave Settlement", "description": "You buy/rent a home specifically near a heritage grocery store and place of worship, even if the commute is longer.", "impact_hint": "Your effective neighborhood density increases significantly.", "score_deltas": {"social_affiliation": 10, "cultural_practice": 8}},
    {"label": "'Only [Language] at Home'", "description": "You establish a rule that only the heritage language is spoken inside your house to prevent further attrition.", "impact_hint": "Language score gets a major boost, as does cultural practice.", "score_deltas": {"language": 15, "cultural_practice": 8}},
    {"label": "Remittance Leadership", "description": "You take over the responsibility of sending money back home and managing family land or businesses in the origin country.", "impact_hint": "Social affiliation and cultural practice strengthen through transnational ties.", "score_deltas": {"social_affiliation": 12, "cultural_practice": 6}},
    {"label": "Intergenerational Co‑living", "description": "You have your parents move in with you. The household becomes a daily site of cultural reinforcement.", "impact_hint": "Language, practice, and social affiliation all improve.", "score_deltas": {"language": 8, "cultural_practice": 12, "social_affiliation": 8}},
    {"label": "Complete Assimilation", "description": "You move to a distant suburb where you are the only one of your background. You stop keeping up with diaspora news.", "impact_hint": "Social affiliation, density, and practice drop sharply.", "score_deltas": {"social_affiliation": -15, "cultural_practice": -12}},
    {"label": "Cultural Mentorship", "description": "You begin volunteering to help newer immigrants from your origin country navigate the system.", "impact_hint": "Social affiliation and self‑presentation improve through purpose.", "score_deltas": {"social_affiliation": 12, "self_presentation": 5}},
    {"label": "Religious Re‑connection", "description": "You return to your heritage mosque/church/temple, viewing it as a social community rather than just a place of worship.", "impact_hint": "Social affiliation and cultural practice rise together.", "score_deltas": {"social_affiliation": 10, "cultural_practice": 8}}
]

# ----------------------------------------------------------------
# SIDEBAR & PROGRESS
# ----------------------------------------------------------------
STAGES = ["Setup", "Research", "Profile", "Arrival", "Adolescence", "Early Adulthood", "Established Life", "Report"]
STAGE_MAP = {
    "setup": 0, "geo_research": 1, "profile": 2,
    "drift_1": 3, "drift_2": 4, "drift_3": 5,
    "drift_4": 6, "reflection": 7
}

def render_progress():
    current = STAGE_MAP.get(st.session_state.get("stage", "setup"), 0)
    steps_html = ""
    for i in range(len(STAGES)):
        cls = "done" if i < current else ("active" if i == current else "")
        steps_html += f'<div class="progress-step {cls}"></div>'
    st.markdown(f'<p class="progress-label">Step {current + 1} of {len(STAGES)} — {STAGES[current]}</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="progress-strip">{steps_html}</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🌍 Cultural Preservation Simulation")
    st.markdown("*An agentic identity trajectory model*")
    st.divider()
    st.markdown("**AI providers**")
    if OPENAI_KEY:
        st.markdown("🟢 OpenAI (primary)")
    else:
        st.markdown("🔴 OpenAI — no key in .env")
    if GROQ_KEY:
        st.markdown("🟢 Groq (fallback)")
    else:
        st.markdown("⚪ Groq — no key in .env")
    if st.session_state.stage != "setup" and st.session_state.trajectory:
        st.divider()
        st.markdown("**Live MR Score**")
        last = st.session_state.trajectory[-1]
        mr = compute_mr(last["scores"])
        color = mr_color(mr)
        st.markdown(f"<span style='font-size:2.2rem;font-weight:800;color:{color}'>{mr}</span> / 100", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{color};font-size:0.85rem'>{mr_label(mr)}</span>", unsafe_allow_html=True)
        st.divider()
        for dim, val in last["scores"].items():
            st.markdown(f"**{dim.replace('_',' ').title()}**: {val}")
            st.progress(val / 100)
    if st.session_state.cfg.get("dest_city"):
        st.divider()
        st.markdown("**Journey**")
        st.markdown(f"📍 {st.session_state.cfg.get('origin_city')}, {st.session_state.cfg.get('origin_country')}")
        st.markdown(f"✈️ {st.session_state.cfg.get('dest_city')}, {st.session_state.cfg.get('dest_country')}")
        st.markdown(f"🗣️ {st.session_state.cfg.get('language')}")
    st.divider()
    with st.expander("🔍 Agent Handoff Traces"):
        if st.session_state.state_snapshots:
            st.write(f"{len(st.session_state.state_snapshots)} handoffs recorded")
            combined = json.dumps(st.session_state.state_snapshots, indent=2)
            st.download_button(
                label="⬇ Download all handoffs (JSON)",
                data=combined,
                file_name=f"handoffs_all_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )
            st.markdown("---")
            st.markdown("**Individual snapshots:**")
            for i, snap in enumerate(st.session_state.state_snapshots):
                snap_json = json.dumps(snap, indent=2)
                filename = f"handoff_{snap['snapshot_name']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json"
                st.download_button(
                    label=f"{i+1}. {snap['snapshot_name']}",
                    data=snap_json,
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True,
                    key=f"download_snap_{i}"
                )
        else:
            st.info("Run simulation to see agent handoff states.")
    if st.button("🔄 Restart"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ----------------------------------------------------------------
# SETUP STAGE
# ----------------------------------------------------------------
if st.session_state.stage == "setup":
    if not GROQ_KEY and not OPENAI_KEY:
        st.error("No API keys detected. Create a `.env` file with OPENAI_API_KEY and/or GROQ_API_KEY.")
        st.code("OPENAI_API_KEY=your_key_here\nGROQ_API_KEY=your_key_here", language="bash")
        st.stop()
    render_progress()
    st.markdown('<div class="chapter-header">Configure the Simulation</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-sub">Define the migration journey. The more specific you are about origin city, destination, and heritage language, the more grounded the simulation becomes.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Origin**")
        origin_country = st.text_input("Country of origin", placeholder="e.g. Nigeria")
        origin_city    = st.text_input("City or region of origin", placeholder="e.g. Lagos")
        language       = st.text_input("Heritage language spoken at home", placeholder="e.g. Yoruba, Igbo, Spanish")
    with col2:
        st.markdown("**Destination**")
        dest_country = st.text_input("Destination country", placeholder="e.g. United States")
        dest_city    = st.text_input("Destination city / state", placeholder="e.g. Columbus, Ohio")

    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        age          = st.slider("Age at migration", 1, 16, 12)
        anchor       = st.slider("Cultural anchor (depth of immersion in origin culture)", 1, 10, 7)
        language_use = st.slider("Heritage language use frequency at home", 1, 10, 6)
        homophily    = st.slider("Social homophily (co-ethnic peer preference)", 1, 10, 5)
    with col4:
        density      = st.select_slider("Neighborhood cultural density", options=["Very low", "Low", "Medium", "High", "Very high"], value="Low")
        institutional = st.toggle("Institutional anchor present (cultural church, association, etc.)")
        transmission  = st.slider("Intergenerational transmission pressure (parental enforcement)", 1, 10, 6)

    st.divider()
    st.markdown("### 📝 What is Cultural retention to you? (optional)")
    st.markdown('<p style="font-size:0.88rem;color:#666;margin-bottom:8px">Write one or two sentences about a specific memory, person, or habit, festival that represents or references your cultural heritage that you\'re very particular about retaining. The more specific the better.</p>', unsafe_allow_html=True)
    biography = st.text_area("Your cultural anchor", placeholder='e.g. "I would love to keep my accent when I move. I would love to be in an environment where I can easily access ingredients to make a specific dish. Attending the lunar festival helps me feel closer to home."', height=90, label_visibility="collapsed")
    st.divider()
    if not all([origin_country, origin_city, dest_country, dest_city, language]):
        st.warning("Please fill in all location and language fields.")
    else:
        if st.button("▶ Run simulation", use_container_width=True):
            st.session_state.cfg = {
                "origin_country": origin_country, "origin_city": origin_city,
                "dest_country": dest_country, "dest_city": dest_city,
                "language": language, "age": age, "anchor": anchor,
                "language_use": language_use, "homophily": homophily,
                "density": density, "institutional": institutional,
                "transmission": transmission,
                "biography": biography.strip() if biography.strip() else ""
            }
            st.session_state.stage = "geo_research"
            st.rerun()

# ----------------------------------------------------------------
# GEO RESEARCH STAGE
# ----------------------------------------------------------------
elif st.session_state.stage == "geo_research":
    render_progress()
    st.markdown('<div class="stage-badge">Geographic Research</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-header">Researching the Community Context</div>', unsafe_allow_html=True)
    cfg = st.session_state.cfg
    st.markdown(f'<div class="chapter-sub">Analyzing the {cfg["origin_country"]} diaspora community in {cfg["dest_city"]}...</div>', unsafe_allow_html=True)

    if "geo_validated" not in st.session_state:
        with st.spinner("Checking geographic plausibility..."):
            plausible, reason = quick_geo_validation(cfg)
        if not plausible:
            st.error(f"⚠️ Geographic plausibility check failed: {reason}")
            st.markdown("**Please correct your origin/destination entries or confirm they are correct.**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Go back and edit"):
                    st.session_state.stage = "setup"
                    st.rerun()
            with col2:
                if st.button("Continue anyway (not recommended)"):
                    st.session_state.geo_validated = "forced"
                    st.rerun()
            st.stop()
        else:
            st.session_state.geo_validated = "passed"
            st.success(f"✓ Geographic plausibility passed: {reason}")
            st.rerun()
    else:
        if not st.session_state.geo_context:
            with st.spinner(f"Analyzing community data for {cfg['dest_city']}..."):
                geo_text, provider = call_llm(geo_research_prompt(cfg), json_mode=False)
            if geo_text.startswith("ERROR"):
                st.error(geo_text)
                st.stop()
            st.session_state.geo_context = geo_text
            st.session_state.geo_provider = provider

            with st.spinner("Organizing community resources..."):
                structured_text, _ = call_llm(geo_structured_prompt(cfg), json_mode=True)
                try:
                    st.session_state.geo_structured = json.loads(structured_text)
                except:
                    st.session_state.geo_structured = {"error": "Could not parse structured data", "raw": structured_text}

        provider = st.session_state.get("geo_provider", "")
        st.markdown(
            f'<div class="geo-box"><strong>Community context: {cfg["origin_city"]} → {cfg["dest_city"]}</strong>'
            f'{provider_badge(provider)}<br><br>{st.session_state.geo_context}</div>',
            unsafe_allow_html=True
        )
        if st.button("Continue to Profile Agent →"):
            st.session_state.stage = "profile"
            st.rerun()

# ----------------------------------------------------------------
# PROFILE AGENT STAGE
# ----------------------------------------------------------------
elif st.session_state.stage == "profile":
    render_progress()
    st.markdown('<div class="stage-badge">Chapter 1 — Profile Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-header">Building the Cultural Baseline</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-sub">The Architect calibrates starting scores using real community context.</div>', unsafe_allow_html=True)

    if "profile_result" not in st.session_state:
        with st.spinner("Profile Agent reasoning..."):
            raw, provider = call_llm(profile_agent_prompt(st.session_state.cfg, st.session_state.geo_context), json_mode=True)
            result = parse_json(raw)
        if not result or "scores" not in result:
            st.error(f"Profile Agent returned invalid JSON. Response: {raw[:600]}")
            st.stop()
        st.session_state.profile_result = result
        st.session_state.profile_provider = provider
        st.session_state.json_state = {
            "scores": result["scores"],
            "resilience_anchors": result.get("resilience_anchors", []),
            "risk_factors": result.get("risk_factors", []),
            "personal_anchor": result.get("personal_anchor", ""),
            "personal_anchor_used": result.get("personal_anchor_used", ""),
            "stage_history": [], "failure_log": [],
            "pivot_choice": None,
            "config": st.session_state.cfg,
            "geo_context": st.session_state.geo_context
        }
        st.session_state.trajectory = [{"stage": "Baseline", "scores": result["scores"]}]
        st.session_state.narratives.append(result.get("narrative", ""))
        record_snapshot("after_profile_agent")

    result = st.session_state.profile_result
    provider = st.session_state.get("profile_provider", "")
    st.markdown(f'<div class="narrative-box">{result.get("narrative", "")}{provider_badge(provider)}</div>', unsafe_allow_html=True)
    if result.get("community_density_assessment"):
        st.markdown(f'<div class="geo-box">🏘️ {result["community_density_assessment"]}</div>', unsafe_allow_html=True)
    if result.get("personal_anchor_used"):
        st.markdown(f'<div class="geo-box">🪝 <strong>Anchor used in simulation:</strong> {result["personal_anchor_used"]}</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Resilience anchors**")
        for a in result.get("resilience_anchors", []):
            st.markdown(f'<div class="anchor-item">✦ {a}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**Risk factors**")
        for r in result.get("risk_factors", []):
            st.markdown(f'<div class="risk-item">⚠ {r}</div>', unsafe_allow_html=True)

    mr = compute_mr(result["scores"])
    st.markdown(f'<div class="mr-score-box {mr_class(mr)}"><div class="mr-num" style="color:{mr_color(mr)}">{mr}</div><div class="mr-label">Starting MR score — {mr_label(mr)}</div></div>', unsafe_allow_html=True)
    st.plotly_chart(build_chart(st.session_state.trajectory), use_container_width=True)
    if st.button("Continue to Stage 1: Arrival →"):
        st.session_state.stage = "drift_1"
        st.rerun()

# ----------------------------------------------------------------
# DRIFT STAGES
# ----------------------------------------------------------------
elif st.session_state.stage == "drift_1":
    run_drift_stage("1", "Arrival", f"Age {st.session_state.cfg['age']} — first year",
                    "Chapter 2 — Drift Agent · Stage 1", "Arrival",
                    "First year in the new country. Everything is unfamiliar.",
                    "drift_2", "Continue to Stage 2: Adolescence")

elif st.session_state.stage == "drift_2":
    run_drift_stage("2", "Adolescence", "Ages 14–18",
                    "Chapter 2 — Drift Agent · Stage 2", "Adolescence",
                    "High school years. Peer pressure. Identity under social scrutiny.",
                    "drift_3", "Continue to Early Adulthood",
                    stage_choices=choices_adolescence)

elif st.session_state.stage == "drift_3":
    run_drift_stage("3", "Early Adulthood", "Ages 18–22",
                    "Chapter 3 — Drift Agent · Stage 3", "Early Adulthood",
                    "College years, first jobs, and independence. You have more agency.",
                    "drift_4", "Continue to Established Life",
                    stage_choices=choices_early_adulthood)

elif st.session_state.stage == "drift_4":
    run_drift_stage("4", "Established Life", "Ages 22–25+",
                    "Chapter 4 — Drift Agent · Stage 4", "Established Life",
                    "Long‑term decisions about where to live, who to love, and what to pass on.",
                    "reflection", "Generate Final Reflection Report",
                    stage_choices=choices_established_life)

# ----------------------------------------------------------------
# REFLECTION STAGE
# ----------------------------------------------------------------
elif st.session_state.stage == "reflection":
    render_progress()
    st.markdown('<div class="stage-badge">Chapter 7 — Reflection Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-header">The Final Report</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-sub">The Analyst synthesizes the full trajectory into research-grade insight.</div>', unsafe_allow_html=True)

    if "reflection_result" not in st.session_state:
        with st.spinner("Reflection Agent generating final analysis..."):
            raw, provider = call_llm(reflection_agent_prompt(
                st.session_state.json_state, st.session_state.trajectory,
                st.session_state.cfg, st.session_state.geo_context
            ), json_mode=True)
            result = parse_json(raw)
        if not result:
            st.error(f"Reflection Agent failed. Response: {raw[:600]}")
            st.stop()
        st.session_state.reflection_result = result
        st.session_state.reflection_provider = provider
        record_snapshot("after_reflection_agent")

    result = st.session_state.reflection_result
    provider = st.session_state.get("reflection_provider", "")
    mr = compute_mr(st.session_state.json_state["scores"])
    st.markdown(f'<div class="mr-score-box {mr_class(mr)}"><div class="mr-num" style="color:{mr_color(mr)}">{mr} / 100</div><div class="mr-label">Final Cultural Preservation Score — {mr_label(mr)}</div></div>', unsafe_allow_html=True)
    st.plotly_chart(build_chart(st.session_state.trajectory), use_container_width=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Narrative", "Turning Points & Drivers", "Counterfactuals", "Research & Data"])

    with tab1:
        st.markdown(f"### Narrative summary {provider_badge(provider)}", unsafe_allow_html=True)
        st.markdown(f'<div class="narrative-box">{result.get("narrative_summary", "")}</div>', unsafe_allow_html=True)
        st.markdown("### Preservation verdict")
        st.markdown(f'<div class="narrative-box">{result.get("preservation_verdict", "")}</div>', unsafe_allow_html=True)
        st.markdown("### Community context used")
        st.markdown(f'<div class="geo-box">{st.session_state.geo_context}</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown("### Critical turning point")
        st.markdown(f'<div class="narrative-box">{result.get("turning_point", "")}</div>', unsafe_allow_html=True)
        st.markdown("### Top 3 drivers")
        for i, d in enumerate(result.get("ranked_drivers", []), 1):
            st.markdown(f'<div class="driver-tag">{i}. {d}</div>', unsafe_allow_html=True)
        if st.session_state.json_state.get("failure_log"):
            st.divider()
            st.markdown("### Tipping point log")
            for entry in st.session_state.json_state["failure_log"]:
                st.error(f"**{entry['stage']}**: {entry['event']}")

    with tab3:
        st.markdown("### Counterfactual A — Alternative destination city")
        st.markdown(f'<div class="narrative-box">{result.get("counterfactual_a", "")}</div>', unsafe_allow_html=True)
        st.markdown("### Counterfactual B — Alternative pivot choice")
        st.markdown(f'<div class="narrative-box">{result.get("counterfactual_b", "")}</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown("### Community Resources & Context")
        geo = st.session_state.get("geo_structured", {})
        if isinstance(geo, dict) and "error" not in geo:
            dp = geo.get("diaspora_presence", {})
            st.markdown(f"**📍 Population & Neighborhoods**")
            st.markdown(f"- Estimate: {dp.get('population_estimate', 'Unknown')}")
            if dp.get("neighborhoods"):
                st.markdown(f"- Concentrated in: {', '.join(dp['neighborhoods'])}")
            st.markdown(f"- {dp.get('notes', '')}")
            inst = geo.get("institutions", {})
            if any(inst.values()):
                st.markdown("**🏛️ Institutions & Resources**")
                col_a, col_b = st.columns(2)
                with col_a:
                    if inst.get("restaurants"):
                        st.markdown(f"🍽️ **Restaurants**: {', '.join(inst['restaurants'])}")
                    if inst.get("places_of_worship"):
                        st.markdown(f"⛪ **Places of worship**: {', '.join(inst['places_of_worship'])}")
                    if inst.get("cultural_centers"):
                        st.markdown(f"🏛️ **Cultural centers**: {', '.join(inst['cultural_centers'])}")
                with col_b:
                    if inst.get("language_schools"):
                        st.markdown(f"📚 **Language schools**: {', '.join(inst['language_schools'])}")
                    if inst.get("annual_events"):
                        st.markdown(f"🎉 **Annual events**: {', '.join(inst['annual_events'])}")
            edu = geo.get("schools_and_universities", {})
            if edu.get("k12_schools_with_diversity") or edu.get("universities_with_cultural_groups"):
                st.markdown("**🎓 Schools & Universities**")
                if edu.get("k12_schools_with_diversity"):
                    st.markdown(f"- K‑12 schools with diverse populations: {', '.join(edu['k12_schools_with_diversity'])}")
                if edu.get("universities_with_cultural_groups"):
                    st.markdown(f"- Universities with cultural groups: {', '.join(edu['universities_with_cultural_groups'])}")
            sim = geo.get("similarities_to_origin", {})
            st.markdown("**🏝️ Similarities to your origin city**")
            st.markdown(f"- **Architecture**: {sim.get('architecture', 'No notable similarities')}")
            st.markdown(f"- **Geography**: {sim.get('geography', 'Different')}")
            st.markdown(f"- **Climate**: {sim.get('climate', 'No comparison provided')}")
            if sim.get("public_spaces"):
                st.markdown(f"- **Public spaces**: {sim['public_spaces']}")
            st.markdown("**📊 Social Climate**")
            st.markdown(f"- **Assimilation pressure**: {geo.get('assimilation_pressure', 'Not specified')}")
            st.markdown(f"- **Community reception**: {geo.get('reception', 'Not specified')}")
        else:
            st.markdown("(Community context could not be structured – raw data below)")
            st.markdown(f'<div class="geo-box">{st.session_state.geo_context}</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("### Full JSON state store (for reference)")
        with st.expander("Click to expand raw JSON"):
            st.json(st.session_state.json_state)
        st.markdown("### Complete trajectory data")
        st.json(st.session_state.trajectory)

    # Export section
    st.divider()
    st.markdown("### 📥 Export this run")
    st.markdown("Download a complete log of this simulation run for your evaluation package.")
    cfg = st.session_state.cfg
    run_log = {
        "run_metadata": {
            "timestamp": datetime.datetime.now().isoformat(),
            "case_label": f"{cfg.get('origin_city')}_{cfg.get('dest_city')}_{cfg.get('age')}".replace(" ", "_"),
            "provider_used": {
                "geo_research": st.session_state.get("geo_provider", "unknown"),
                "profile_agent": st.session_state.get("profile_provider", "unknown"),
                "drift_stage_1": st.session_state.get("provider_1", "unknown"),
                "drift_stage_2": st.session_state.get("provider_2", "unknown"),
                "drift_stage_3": st.session_state.get("provider_3", "unknown"),
                "drift_stage_4": st.session_state.get("provider_4", "unknown"),
                "reflection_agent": st.session_state.get("reflection_provider", "unknown"),
            }
        },
        "input_configuration": cfg,
        "geo_context": st.session_state.geo_context,
        "final_mr_score": compute_mr(st.session_state.json_state["scores"]),
        "final_scores": st.session_state.json_state["scores"],
        "trajectory": st.session_state.trajectory,
        "stage_history": st.session_state.json_state.get("stage_history", []),
        "failure_log": st.session_state.json_state.get("failure_log", []),
        "resilience_anchors": st.session_state.json_state.get("resilience_anchors", []),
        "risk_factors": st.session_state.json_state.get("risk_factors", []),
        "pivot_choice": st.session_state.json_state.get("pivot_choice", ""),
        "reflection_report": result,
    }
    filename = f"run_{run_log['run_metadata']['case_label']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json"
    st.download_button(label="⬇ Download run log (JSON)", data=json.dumps(run_log, indent=2), file_name=filename, mime="application/json", use_container_width=True)
    st.caption("Save this file and name it appropriately. You can inspect them for closer evaluation.")
    st.divider()
    if st.button("↩ Run a new simulation", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()