import streamlit as st
from openai import OpenAI
import json
import os
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Roots & Drift",
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
    .pivot-card {
        background: #1e1e2e; border: 1px solid #444466;
        border-radius: 10px; padding: 16px 20px; margin-bottom: 12px;
    }
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

# ═══════════════════════════════════════════════════════════════
# LLM CALLER — Groq primary, OpenAI fallback
# Keys loaded from .env — never from the UI
# ═══════════════════════════════════════════════════════════════
GROQ_KEY   = os.getenv("GROQ_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

def call_llm(prompt: str, json_mode: bool = True) -> tuple[str, str]:
    """
    Returns (response_text, provider_used).
    Tries Groq first, falls back to OpenAI if Groq fails.
    json_mode=True forces JSON output (used for all agents).
    json_mode=False returns plain text (used for geo research).
    """
    providers = []
    if GROQ_KEY:
        providers.append(("Groq", OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_KEY
        ), "llama-3.3-70b-versatile"))
    if OPENAI_KEY:
        providers.append(("OpenAI", OpenAI(api_key=OPENAI_KEY), "gpt-4o-mini"))

    if not providers:
        return "ERROR: No API keys found. Add GROQ_API_KEY or OPENAI_API_KEY to your .env file.", ""

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
    cls = "groq-badge" if provider == "Groq" else "openai-badge"
    return f'<span class="provider-badge {cls}">via {provider}</span>'

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "stage": "setup", "json_state": {}, "trajectory": [],
        "narratives": [], "pivot_choice": None,
        "geo_context": "", "cfg": {}, "providers_used": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ═══════════════════════════════════════════════════════════════
# CHART
# ═══════════════════════════════════════════════════════════════
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
        line=dict(color="#ffffff", width=3, dash="dash")
    ))
    fig.update_layout(
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        font=dict(color="#ccccdd"),
        legend=dict(bgcolor="#1a1a2e", bordercolor="#333355"),
        xaxis=dict(gridcolor="#222233", title="Life stage"),
        yaxis=dict(gridcolor="#222233", title="Score (0–100)", range=[0, 100]),
        margin=dict(l=40, r=20, t=30, b=40), height=340,
    )
    return fig

# ═══════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════
def geo_research_prompt(cfg: dict) -> str:
    return f"""You are a cultural geography researcher with deep knowledge of global diaspora communities.

Migration context:
- Origin: {cfg['origin_city']}, {cfg['origin_country']}
- Destination: {cfg['dest_city']}, {cfg['dest_country']}
- Heritage language: {cfg['language']}

Using your knowledge, synthesize a specific, grounded description covering:
1. Approximate size and density of the {cfg['origin_country']} diaspora in {cfg['dest_city']}
2. Known cultural institutions (churches, associations, cultural centers, restaurants, community events)
3. General immigrant experience and reception for this group in {cfg['dest_city']}
4. How culturally isolated vs well-supported this destination tends to be for this group
5. Any notable cultural neighborhoods, corridors, or community hubs

Be specific. Name real organizations or neighborhoods where you know them.
Be honest about uncertainty where your knowledge is limited.
Write 5-6 sentences as a plain text paragraph. No JSON. No bullet points. No headers."""

def profile_agent_prompt(cfg: dict, geo_context: str) -> str:
    return f"""You are the Profile Agent in a cultural preservation simulation. Persona: "The Architect."
Translate sociological variables into a culturally grounded baseline, informed by real geographic context.

GEOGRAPHIC AND COMMUNITY CONTEXT:
{geo_context}

User configuration:
- Origin: {cfg['origin_city']}, {cfg['origin_country']}
- Destination: {cfg['dest_city']}, {cfg['dest_country']}
- Heritage language: {cfg['language']}
- Age at migration: {cfg['age']}
- Cultural anchor (1-10): {cfg['anchor']}
- Heritage language use at home (1-10): {cfg['language_use']}
- Social homophily — co-ethnic peer preference (1-10): {cfg['homophily']}
- Neighborhood cultural density: {cfg['density']}
- Institutional anchor present: {cfg['institutional']}
- Intergenerational transmission pressure (1-10): {cfg['transmission']}

Use the geographic context to calibrate scores. A city with a large organized diaspora produces higher social affiliation scores than a culturally sparse one.
Write a 4-5 sentence narrative in second person. Name the destination city. Make it feel real and specific.

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
  "community_density_assessment": "<one sentence on geographic support level>",
  "narrative": "<4-5 sentence second-person narrative>"
}}"""

def drift_agent_prompt(state: dict, stage_name: str, stage_ages: str, cfg: dict, pivot: str = None) -> str:
    pivot_ctx = f"\nIMPORTANT: At age 18 this person chose a life pivot: '{pivot}'. This must meaningfully shift at least one dimension — not a cosmetic change." if pivot else ""
    return f"""You are the Drift Simulation Agent. Persona: "The Simulator."
Model compounding cultural pressure across life stages with sociological accuracy.

Geographic context: {cfg['origin_city']}, {cfg['origin_country']} → {cfg['dest_city']}, {cfg['dest_country']}
Heritage language: {cfg['language']}

Current JSON state:
{json.dumps(state, indent=2)}

Life stage: {stage_name} ({stage_ages})
{pivot_ctx}

Rules:
- Scores compound from prior stage. Never reset to baseline.
- Avoid smooth linear drift. Allow sudden drops, stagnation, or partial recovery.
- If institutional anchors are present and this is Early Adulthood, a Cultural Re-awakening (score increase) is possible.
- Reference geographic context in the narrative where relevant.
- Identify the single most influential variable this stage.
- Flag tipping points: any dimension dropping more than 15 points.
- Write a 4-5 sentence narrative in second person, naming the city.

Return ONLY valid JSON:
{{
  "scores": {{
    "language": <int 0-100>,
    "cultural_practice": <int 0-100>,
    "social_affiliation": <int 0-100>,
    "self_presentation": <int 0-100>
  }},
  "primary_driver": "<variable and brief explanation>",
  "narrative": "<4-5 sentence second-person narrative>",
  "failure_log": "<empty string, or tipping point description>"
}}"""

def reflection_agent_prompt(state: dict, trajectory: list, cfg: dict, geo_context: str) -> str:
    return f"""You are the Reflection Agent. Persona: "The Analyst."
Produce rigorous, evidence-based synthesis. No generic summaries.

Geographic context: {cfg['origin_city']}, {cfg['origin_country']} → {cfg['dest_city']}, {cfg['dest_country']}
Heritage language: {cfg['language']}
Community context: {geo_context}

Full trajectory:
{json.dumps(trajectory, indent=2)}

Final state:
{json.dumps(state, indent=2)}

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

# ═══════════════════════════════════════════════════════════════
# DRIFT HELPER
# ═══════════════════════════════════════════════════════════════
def run_drift_stage(stage_key, stage_name, stage_ages, badge, title, sub, next_stage, next_label, pivot=None):
    st.markdown(f'<div class="stage-badge">{badge}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chapter-header">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chapter-sub">{sub}</div>', unsafe_allow_html=True)

    cache_key = f"drift_result_{stage_key}"
    if cache_key not in st.session_state:
        with st.spinner(f"Drift Agent simulating {stage_name}..."):
            prompt = drift_agent_prompt(
                st.session_state.json_state, stage_name, stage_ages,
                st.session_state.cfg, pivot
            )
            raw, provider = call_llm(prompt, json_mode=True)
            result = parse_json(raw)

        if not result or "scores" not in result:
            st.error(f"Drift Agent failed. Response: {raw[:600]}")
            st.stop()

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

    result   = st.session_state[cache_key]
    provider = st.session_state.get(f"provider_{stage_key}", "")

    st.markdown(
        f'<div class="narrative-box">{result.get("narrative", "")}'
        f'{provider_badge(provider)}</div>',
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="driver-tag">Primary driver: {result.get("primary_driver", "")}</div>', unsafe_allow_html=True)
    if result.get("failure_log"):
        st.warning(f"Tipping point detected: {result['failure_log']}")

    mr = compute_mr(result["scores"])
    st.markdown(f'<div class="mr-score-box {mr_class(mr)}"><div class="mr-num" style="color:{mr_color(mr)}">{mr}</div><div class="mr-label">MR after {stage_name} — {mr_label(mr)}</div></div>', unsafe_allow_html=True)
    st.plotly_chart(build_chart(st.session_state.trajectory), use_container_width=True)

    if st.button(f"{next_label} →", key=f"btn_{stage_key}"):
        st.session_state.stage = next_stage
        st.rerun()

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🌍 Roots & Drift")
    st.markdown("*A cultural preservation simulation*")

    # Show which providers are active — no keys displayed
    st.divider()
    st.markdown("**AI providers**")
    if GROQ_KEY:
        st.markdown("🟢 Groq (primary)")
    else:
        st.markdown("🔴 Groq — no key in .env")
    if OPENAI_KEY:
        st.markdown("🟢 OpenAI (fallback)")
    else:
        st.markdown("⚪ OpenAI — no key in .env")

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
    if st.button("🔄 Restart"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ═══════════════════════════════════════════════════════════════
# STAGE 0 — SETUP
# ═══════════════════════════════════════════════════════════════
if st.session_state.stage == "setup":
    # Key check before showing the form
    if not GROQ_KEY and not OPENAI_KEY:
        st.error("No API keys detected. Create a `.env` file in this folder with GROQ_API_KEY and/or OPENAI_API_KEY.")
        st.code("GROQ_API_KEY=your_key_here\nOPENAI_API_KEY=your_key_here", language="bash")
        st.stop()

    st.markdown('<div class="chapter-header">Configure the Simulation</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-sub">Define the migration journey. The more specific the location, the more grounded the story.</div>', unsafe_allow_html=True)

    st.markdown("### 📍 The journey")
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
    st.markdown("### 🎛️ Sociological variables")
    col3, col4 = st.columns(2)
    with col3:
        age          = st.slider("Age at migration", 0, 16, 5)
        anchor       = st.slider("Cultural anchor (depth of immersion in origin culture)", 1, 10, 7)
        language_use = st.slider("Heritage language use frequency at home", 1, 10, 6)
        homophily    = st.slider("Social homophily (co-ethnic peer preference)", 1, 10, 5)
    with col4:
        density      = st.select_slider("Neighborhood cultural density",
                                        options=["Very low", "Low", "Medium", "High", "Very high"], value="Low")
        institutional = st.toggle("Institutional anchor present (cultural church, association, etc.)")
        transmission  = st.slider("Intergenerational transmission pressure (parental enforcement)", 1, 10, 6)

    st.divider()
    if not all([origin_country, origin_city, dest_country, dest_city, language]):
        st.warning("Please fill in all location and language fields.")
    else:
        if st.button("▶  Run simulation", use_container_width=True):
            st.session_state.cfg = {
                "origin_country": origin_country, "origin_city": origin_city,
                "dest_country": dest_country, "dest_city": dest_city,
                "language": language, "age": age, "anchor": anchor,
                "language_use": language_use, "homophily": homophily,
                "density": density, "institutional": institutional,
                "transmission": transmission
            }
            st.session_state.stage = "geo_research"
            st.rerun()

# ═══════════════════════════════════════════════════════════════
# GEO RESEARCH
# ═══════════════════════════════════════════════════════════════
elif st.session_state.stage == "geo_research":
    st.markdown('<div class="stage-badge">Geographic Research</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-header">Researching the Community Context</div>', unsafe_allow_html=True)
    cfg = st.session_state.cfg
    st.markdown(f'<div class="chapter-sub">Analyzing the {cfg["origin_country"]} diaspora community in {cfg["dest_city"]}...</div>', unsafe_allow_html=True)

    if not st.session_state.geo_context:
        with st.spinner(f"Analyzing community data for {cfg['dest_city']}..."):
            # Geo research is plain text — json_mode=False
            geo_text, provider = call_llm(geo_research_prompt(cfg), json_mode=False)
        if geo_text.startswith("ERROR"):
            st.error(geo_text)
            st.stop()
        st.session_state.geo_context = geo_text
        st.session_state.geo_provider = provider

    provider = st.session_state.get("geo_provider", "")
    st.markdown(
        f'<div class="geo-box"><strong>Community context: {cfg["origin_city"]} → {cfg["dest_city"]}</strong>'
        f'{provider_badge(provider)}<br><br>{st.session_state.geo_context}</div>',
        unsafe_allow_html=True
    )

    if st.button("Continue to Profile Agent →"):
        st.session_state.stage = "profile"
        st.rerun()

# ═══════════════════════════════════════════════════════════════
# PROFILE AGENT
# ═══════════════════════════════════════════════════════════════
elif st.session_state.stage == "profile":
    st.markdown('<div class="stage-badge">Chapter 1 — Profile Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-header">Building the Cultural Baseline</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-sub">The Architect calibrates starting scores using real community context.</div>', unsafe_allow_html=True)

    if "profile_result" not in st.session_state:
        with st.spinner("Profile Agent reasoning..."):
            raw, provider = call_llm(
                profile_agent_prompt(st.session_state.cfg, st.session_state.geo_context),
                json_mode=True
            )
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
            "stage_history": [], "failure_log": [],
            "pivot_choice": None,
            "config": st.session_state.cfg,
            "geo_context": st.session_state.geo_context
        }
        st.session_state.trajectory = [{"stage": "Baseline", "scores": result["scores"]}]
        st.session_state.narratives.append(result.get("narrative", ""))

    result   = st.session_state.profile_result
    provider = st.session_state.get("profile_provider", "")

    st.markdown(
        f'<div class="narrative-box">{result.get("narrative", "")}'
        f'{provider_badge(provider)}</div>',
        unsafe_allow_html=True
    )
    if result.get("community_density_assessment"):
        st.markdown(f'<div class="geo-box">🏘️ {result["community_density_assessment"]}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Resilience anchors**")
        for a in result.get("resilience_anchors", []):
            st.markdown(f"✦ {a}")
    with col2:
        st.markdown("**Risk factors**")
        for r in result.get("risk_factors", []):
            st.markdown(f"⚠ {r}")

    mr = compute_mr(result["scores"])
    st.markdown(f'<div class="mr-score-box {mr_class(mr)}"><div class="mr-num" style="color:{mr_color(mr)}">{mr}</div><div class="mr-label">Starting MR score — {mr_label(mr)}</div></div>', unsafe_allow_html=True)
    st.plotly_chart(build_chart(st.session_state.trajectory), use_container_width=True)

    if st.button("Continue to Stage 1: Arrival →"):
        st.session_state.stage = "drift_1"
        st.rerun()

# ═══════════════════════════════════════════════════════════════
# DRIFT STAGES 1 & 2
# ═══════════════════════════════════════════════════════════════
elif st.session_state.stage == "drift_1":
    run_drift_stage("1", "Arrival", f"Age {st.session_state.cfg['age']} — first year",
                    "Chapter 2 — Drift Agent · Stage 1", "Arrival",
                    "First year in the new country. Everything is unfamiliar.",
                    "drift_2", "Continue to Stage 2: Adolescence")

elif st.session_state.stage == "drift_2":
    run_drift_stage("2", "Adolescence", "Ages 14–18",
                    "Chapter 3 — Drift Agent · Stage 2", "Adolescence",
                    "High school years. Peer pressure. Identity under social scrutiny.",
                    "pivot", "Continue to The Pivot")

# ═══════════════════════════════════════════════════════════════
# PIVOT — HUMAN IN THE LOOP
# ═══════════════════════════════════════════════════════════════
elif st.session_state.stage == "pivot":
    st.markdown('<div class="stage-badge">Chapter 4 — Human Pivot · Age 18</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-header">The Crossroads</div>', unsafe_allow_html=True)

    mr = compute_mr(st.session_state.json_state["scores"])
    st.markdown(f'<div class="mr-score-box {mr_class(mr)}"><div class="mr-num" style="color:{mr_color(mr)}">{mr}</div><div class="mr-label">Current MR at age 18 — {mr_label(mr)}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="narrative-box">The simulation pauses. Structural drift has shaped this person through childhood and adolescence. Now at 18, they face a decision that will determine whether heritage is recovered, stabilized, or lost further. Choose a life path to resume.</div>', unsafe_allow_html=True)
    st.plotly_chart(build_chart(st.session_state.trajectory), use_container_width=True)

    st.divider()
    st.markdown("**Select a life pivot:**")
    pivots = [
        ("🤝 Community anchor", "Join a co-ethnic cultural organization or diaspora community group. Regular engagement with heritage peers, cultural events, and language practice."),
        ("✈️ Heritage reconnection", "Begin making annual visits back to the origin country. Sustained contact with family, language, and cultural environment."),
        ("💼 Professional assimilation", "Prioritize multicultural professional networking. Social circle becomes predominantly host-culture with limited co-ethnic engagement."),
        ("💍 Interethnic partnership", "Enter a long-term relationship with someone from the same heritage culture. Shared household becomes a cultural preservation mechanism."),
    ]
    cols = st.columns(2)
    for i, (label, desc) in enumerate(pivots):
        with cols[i % 2]:
            st.markdown(f'<div class="pivot-card"><strong>{label}</strong><br><span style="color:#aaaaaa;font-size:0.88rem">{desc}</span></div>', unsafe_allow_html=True)
            if st.button(f"Choose: {label}", key=f"pivot_{i}"):
                choice = f"{label} — {desc}"
                st.session_state.pivot_choice = choice
                st.session_state.json_state["pivot_choice"] = choice
                st.session_state.stage = "drift_3"
                st.rerun()

# ═══════════════════════════════════════════════════════════════
# DRIFT STAGES 3 & 4
# ═══════════════════════════════════════════════════════════════
elif st.session_state.stage == "drift_3":
    pivot_short = st.session_state.pivot_choice.split("—")[0].strip() if st.session_state.pivot_choice else ""
    run_drift_stage("3", "Early Adulthood", "Ages 18–22",
                    "Chapter 5 — Drift Agent · Stage 3", "Early Adulthood",
                    f"Pivot applied: {pivot_short}. College years and early independence.",
                    "drift_4", "Continue to Stage 4: Established Life",
                    pivot=st.session_state.pivot_choice)

elif st.session_state.stage == "drift_4":
    run_drift_stage("4", "Established Life", "Ages 22–25",
                    "Chapter 6 — Drift Agent · Stage 4", "Established Life",
                    "Identity stabilizes. Patterns become harder to reverse.",
                    "reflection", "Generate Final Reflection Report",
                    pivot=st.session_state.pivot_choice)

# ═══════════════════════════════════════════════════════════════
# REFLECTION AGENT
# ═══════════════════════════════════════════════════════════════
elif st.session_state.stage == "reflection":
    st.markdown('<div class="stage-badge">Chapter 7 — Reflection Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-header">The Final Report</div>', unsafe_allow_html=True)
    st.markdown('<div class="chapter-sub">The Analyst synthesizes the full trajectory into research-grade insight.</div>', unsafe_allow_html=True)

    if "reflection_result" not in st.session_state:
        with st.spinner("Reflection Agent generating final analysis..."):
            raw, provider = call_llm(
                reflection_agent_prompt(
                    st.session_state.json_state, st.session_state.trajectory,
                    st.session_state.cfg, st.session_state.geo_context
                ),
                json_mode=True
            )
            result = parse_json(raw)
        if not result:
            st.error(f"Reflection Agent failed. Response: {raw[:600]}")
            st.stop()
        st.session_state.reflection_result = result
        st.session_state.reflection_provider = provider

    result   = st.session_state.reflection_result
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
        st.markdown("### Research note")
        st.markdown(f'<div class="narrative-box">{result.get("research_note", "")}</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Full JSON state store")
        st.json(st.session_state.json_state)
        st.markdown("### Complete trajectory data")
        st.json(st.session_state.trajectory)

    st.divider()
    if st.button("↩ Run a new simulation", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()