import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import copy
import datetime

load_dotenv()

# ----------------------------------------------------------------
# LLM CALLER (OpenAI primary, Groq fallback)
# ----------------------------------------------------------------
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

def call_llm(prompt: str, json_mode: bool = True) -> tuple[str, str]:
    providers = []
    if OPENAI_KEY:
        providers.append(("OpenAI", OpenAI(api_key=OPENAI_KEY), "gpt-4o-mini"))
    if GROQ_KEY:
        providers.append(("Groq", OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY), "llama-3.3-70b-versatile"))
    if not providers:
        return "ERROR: No API keys found.", ""
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

# ----------------------------------------------------------------
# PROMPTS (copied exactly from your try5.py)
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
# CHOICE SETS
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
# CORE SIMULATION RUNNER (no UI)
# ----------------------------------------------------------------
def run_full_simulation(cfg, forced_choices=None):
    # 1. Geographic research
    geo_text, _ = call_llm(geo_research_prompt(cfg), json_mode=False)
    structured_text, _ = call_llm(geo_structured_prompt(cfg), json_mode=True)
    geo_structured = json.loads(structured_text)
    
    # 2. Profile agent
    raw, _ = call_llm(profile_agent_prompt(cfg, geo_text), json_mode=True)
    profile = parse_json(raw)
    
    # 3. Initialize state
    state = {
        "scores": profile["scores"],
        "resilience_anchors": profile.get("resilience_anchors", []),
        "risk_factors": profile.get("risk_factors", []),
        "personal_anchor_used": profile.get("personal_anchor_used", ""),
        "stage_history": [{"stage": "Baseline", **profile}],
        "failure_log": [],
        "config": cfg,
        "geo_context": geo_text,
        "geo_structured": geo_structured,
        "tipping_point_occurred": False
    }
    trajectory = [{"stage": "Baseline", "scores": profile["scores"]}]
    
    # 4. Stage definitions
    stages = [
        ("Arrival", f"Age {cfg['age']} — first year", False),
        ("Adolescence", "Ages 14–18", True),
        ("Early Adulthood", "Ages 18–22", True),
        ("Established Life", "Ages 22–25+", True)
    ]
    
    choice_sets = {
        "Adolescence": choices_adolescence,
        "Early Adulthood": choices_early_adulthood,
        "Established Life": choices_established_life
    }
    
    for stage_name, stage_ages, has_choices in stages:
        # Drift agent
        prompt = drift_agent_prompt(state, stage_name, stage_ages, cfg, pivot=None)
        raw, _ = call_llm(prompt, json_mode=True)
        drift = parse_json(raw)
        
        # Handle missing scores
        if not isinstance(drift, dict) or "scores" not in drift:
            print(f"\n❌ Drift Agent failed for {stage_name}. Raw response:\n{raw[:300]}\n")
            # Fallback: keep previous scores
            drift = {
                "scores": state["scores"].copy(),
                "primary_driver": "LLM error – no valid response",
                "narrative": "The simulation encountered a technical error.",
                "failure_log": "LLM response missing 'scores'"
            }
        
        # Save pre‑choice scores for delta check
        old_scores = state["scores"].copy()
        
        # Update state with drift output
        state["scores"] = drift["scores"]
        state["stage_history"].append({"stage": stage_name, **drift})
        if drift.get("failure_log"):
            state["failure_log"].append({"stage": stage_name, "event": drift["failure_log"]})
        trajectory.append({"stage": stage_name, "scores": drift["scores"]})
        
        # Apply forced choices if provided for this stage
        if has_choices and forced_choices and stage_name in forced_choices and forced_choices[stage_name]:
            choices = forced_choices[stage_name]
            stage_choices = choice_sets[stage_name]
            baseline = state["scores"].copy()
            total_delta = {"language": 0, "cultural_practice": 0, "social_affiliation": 0, "self_presentation": 0}
            n = len(choices)
            scale = 1.0 if n == 1 else 0.7 if n == 2 else 0.5
            for label in choices:
                for ch in stage_choices:
                    if ch["label"] == label and "score_deltas" in ch:
                        for dim, delta in ch["score_deltas"].items():
                            total_delta[dim] += int(delta * scale)
            new_scores = {}
            for dim in total_delta:
                new_val = baseline.get(dim, 50) + total_delta[dim]
                new_scores[dim] = max(0, min(100, new_val))
            state["scores"] = new_scores
            trajectory[-1]["scores"] = new_scores
            state["stage_history"][-1]["user_choices"] = choices
            trajectory[-1]["choices"] = choices
        
        # Check for tipping point (>15 drop)
        for dim in old_scores:
            old = old_scores.get(dim, 50)
            new = state["scores"].get(dim, 50)
            if old - new > 15:
                state["tipping_point_occurred"] = True
                break
    
    # 5. Reflection agent
    raw, _ = call_llm(reflection_agent_prompt(state, trajectory, cfg, geo_text), json_mode=True)
    reflection = parse_json(raw)
    
    return state, reflection, trajectory