# Cultural Preservation Simulation Agent
### An Agentic Simulation of Cultural Identity Preservation and Erosion Among First-Generation Immigrants

**Author:** Iteoluwa Ibitoye
**Course:** Agentic Technologies, Spring 2026
**Track:** B — Applied Agent Experience
**Demo:** https://youtu.be/E_No8F_kTJQ

---

## What This Is

The Cultural Preservation Simulation Agent is an interactive agentic simulation that models how cultural identity erodes or is preserved among Yyounger immigrants who typically migrate during adolescence (ages 5–16). Users configure a migration profile — origin, destination, heritage language, age at migration, and eight sociological variables — and the system traces how four dimensions of cultural identity evolve across four life stages from arrival through age 25.

The system is powered by three coordinated AI agents:
- **Profile Agent (The Architect)** — builds a culturally grounded baseline from user inputs and geographic research
- **Drift Simulation Agent (The Simulator)** — models compounding identity change across four life stages with user choices at each stage
- **Reflection Agent (The Analyst)** — synthesizes the full trajectory into a final report with counterfactuals, ranked drivers, and a Cultural Preservation Score (MR)

The goal is not to prescribe outcomes but to reveal which factors most accelerate or slow cultural erosion, and what interventions produce meaningfully different trajectories.

---

## Team Members

| Name | Role |
|---|---|
| Iteoluwa Ibitoye | Solo — all phases |

---

## Track

**Track B: Applied Agent Experience**

---

## Setup Instructions

### Requirements
- Python 3.9 or higher
- At least one API key (OpenAI is primary, Groq is fallback)

### Step 1: Get the project files

Make sure the following are in the same folder:

```
full_simulation_app.py
requirements.txt
.env                  ← you create this (see Step 2)
```

### Step 2: Create your .env file

In the same folder as `full_simulation_app.py`, create a file called `.env`:

```
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
```

You need at least one key. OpenAI GPT-4o Mini is the primary provider. Groq Llama 3.3 70B is the fallback. If only one key is available, the simulation will use whichever is present.

**Getting an OpenAI API key:**
1. Go to platform.openai.com
2. Navigate to API Keys and create a new key
3. Note: requires a paid account with credits

**Getting a free Groq API key:**
1. Go to console.groq.com
2. Sign in and click API Keys in the sidebar
3. Click Create API Key and copy it

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the app

```bash
streamlit run full_simulation_app.py
```

The app opens in your browser automatically at `http://localhost:8501`.

---

## How to Run the Simulation

1. **Setup screen** — Enter origin country, origin city, destination country, destination city, and heritage language. Adjust the eight sociological sliders. Optionally write a personal cultural memory in the biography field. Click Run Simulation.

2. **Geographic research** — The system validates the origin/destination pair for plausibility, then researches the diaspora community at the destination city. A community context summary appears.

3. **Profile Agent (Chapter 1)** — Builds a cultural baseline. Starting scores for four dimensions appear alongside resilience anchors, risk factors, and an opening narrative. The MR score initializes here.

4. **Drift Stage 1: Arrival** — Models the first year. No user choices at this stage.

5. **Drift Stage 2: Adolescence** — Models high school years. Select up to 3 life choices from the checkbox panel.

6. **Drift Stage 3: Early Adulthood** — College years and early independence. Select up to 3 more choices.

7. **Drift Stage 4: Established Life** — Long-term identity decisions. Select up to 3 final choices.

8. **Final Report** — The Reflection Agent produces a tabbed report covering Narrative, Turning Points and Drivers, Counterfactuals, and Research and Data. Download the full run log as JSON from the export section at the bottom.

The **Agent Handoff Traces** panel in the sidebar lets you download individual agent state snapshots at any point during the simulation.

---

## Required Dependencies

| Package | Purpose |
|---|---|
| streamlit | Frontend and session state management |
| openai | Unified client for OpenAI and Groq API calls |
| plotly | Interactive trajectory chart |
| python-dotenv | Loading API keys from .env file |

See `requirements.txt` for pinned versions.

---

## Folder Guide

```
team-project/
  README.md                        This file
  AI_USAGE.md                      Full AI usage disclosure
  requirements.txt                 Python dependencies
  .env                             Safe template showing .env format
  docs/
    iibitoye_Finalpacket.pdf       Phase 3 final report containing architecture diagram and One-paragraph project summary          
    screenshots/
      01_home.png                  Setup / landing screen
      02_main_flow.png             Mid-simulation drift stage with choices
      03_evidence_view.png         Research and Data tab (community resources)
      04_history_or_state.png      Agent Handoff Traces panel in sidebar
      05_export_or_artifact.png    JSON export screen
      06_evaluation_view.png       Final MR score and trajectory chart
      07_source_view.png           Geographic community context display
      08_failure_case.png          Critical erosion boundary case (TC-05)
      screenshot_index.md          Screenshot captions and report references
  src/
    full_simulation_app.py         Main Streamlit application
  eval/
    aautomated_evaluation.py       Automated evaluation script (runs TC-01 to TC-10)
    test_cases.csv                 All 10 test case definitions with input configs
    test_cases.md                  Human-readable test case documentation
    evaluation_results.csv         Results for all 10 cases (3 runs each, modal outcome)
    failure_log.md                 Documented failure cases with root causes and status
    version_notes.md               Version history and what changed after each iteration
  outputs/
    demo_outputs/                  Outputs generated during the demo video
    exported_artifacts/            JSON run logs downloaded during test cases
    sample_runs/                   Representative runs few user journeys
  media/
    demo_video_link.txt            Shareable link to the 5-minute demo video
  phase_submissions/
    phase1/                        Phase 1 submission materials
    phase2/                        Phase 2 submission materials
    phase3/                        Phase 3 submission materials
```

---

## Summary of Evaluation Materials

The evaluation covers 10 test scenarios. Each was run three times using `evaluate.py` and the modal outcome (majority pass/fail) is reported. Full details in `eval/evaluation_results.csv`.

| Case | Scenario | Outcome |
|---|---|---|
| TC-01 | The Late Arrival | ✅ PASS — Language = 70 |
| TC-02 | The Child Migrant | ✅ PASS — Language = 15 |
| TC-03 | Institutional Buffer | ❌ FAIL — Delta = 10, below threshold |
| TC-04 | Pivot Divergence | ✅ PASS — SA Δ = 37, CP Δ = 22 |
| TC-05 | Structural Inertia | ✅ PASS — MR = 8.3, impact = 1.3 |
| TC-06 | Cross-Cultural Validity | ❌ FAIL — Only 1 dimension diverged |
| TC-07 | Personalisation Fidelity | ✅ PASS — MR Δ = 8.3 |
| TC-08 | Counterfactual Specificity | ❌ FAIL — Score = 2/5 |
| TC-09 | Tipping-Point Detection | ✅ PASS — Detected correctly |
| TC-10 | Sensory Threading | ❌ FAIL — Keywords not found in narratives |

Overall pass rate: **6/10 (60%)**. The four failures cluster around cross-cultural distinction and sensory narrative threading. Full interpretation in the Phase 3 final report Section 5.

---

## Summary of Outputs Included

- `outputs/sample_runs/` — JSON run logs for representative test cases
- `outputs/exported_artifacts/` — Final reports showing Strong Preservation, Pivot Divergence, and Critical Erosion outcomes
- `outputs/demo_outputs/` — Outputs generated during the demo video walkthrough

---

## Known Limitations

**Cultural overgeneralization:** The system produces weaker distinctions between diaspora groups that are less documented in LLM training data. Nigerian and Mexican communities in Houston produced similar-sounding trajectories despite real sociological differences (TC-06 failure).

**Sensory threading:** Biography keywords do not reliably appear across all stage narratives. The Profile Agent extracts the anchor correctly but the Drift Agent does not always carry it forward explicitly (TC-10 failure).

**Counterfactual vagueness:** The Reflection Agent produces counterfactuals that are directionally correct but often lack specific numeric estimates and named real institutions (TC-08, scored 2/5).

**Institutional buffer effect:** The institutional anchor variable produces a measurable but weaker-than-expected effect on Cultural Practice. The delta of 10 points fell below the 15-point threshold (TC-03 failure).

**No empirical score calibration:** The MR formula and thresholds were set heuristically. Results should be interpreted as directionally indicative, not empirically validated against longitudinal assimilation research.

**Session-based only:** All data is stored in Streamlit session state and cleared on browser close. No cross-session comparison is supported.
