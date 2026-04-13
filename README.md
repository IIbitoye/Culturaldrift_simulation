# Roots & Drift
### An Agentic Simulation of Cultural Preservation and Erosion Among First-Generation Immigrants

**Author:** Iteoluwa Ibitoye  
**Course:** Agentic Technologies, Spring 2026  
**Track:** B — Applied Agent Experience  
**Phase:** 2 Prototype Submission

---

## What This Is

Roots & Drift is an interactive simulation that models how cultural identity changes over time for first-generation immigrants who migrate during adolescence. The user sets up a migration profile — where they came from, where they moved to, what language they speak at home, how old they were when they arrived — and the system traces how four dimensions of cultural identity evolve across four life stages from arrival through age 25.

The simulation is powered by three AI agents (Profile Agent, Drift Simulation Agent, and Reflection Agent) that hand off structured JSON state to each other sequentially. There is one human intervention point at age 18 where the user makes a life pivot choice that affects the rest of the trajectory. The final output is a tabbed report with a narrative summary, turning point analysis, driver rankings, and two counterfactual scenarios.

---

## Quick Start

### Step 1: Clone or download the project

Make sure you have these files in the same folder:

```
roots_and_drift_app.py
requirements.txt
.env              ← you create this (see Step 3)
```

### Step 2: Install dependencies

Python 3.9 or higher is required.

```bash
pip install -r requirements.txt
```

### Step 3: Set up your API keys

Create a file called `.env` in the same folder as the app. It should look like this:

```
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here
```

You need at least one of these. Groq is the primary provider and OpenAI is the fallback. The app will tell you in the sidebar which providers are active.

**Getting a free Groq API key (recommended, takes 2 minutes):**
1. Go to console.groq.com
2. Sign in with Google or create an account
3. Click API Keys in the left sidebar
4. Click Create API Key and copy it

**Getting an OpenAI API key (optional fallback):**
1. Go to platform.openai.com
2. Go to API Keys and create a new key
3. Note: OpenAI requires a paid account with credits

Keys are loaded from the `.env` file automatically. They never appear in the app UI and should never be committed to version control.

### Step 4: Run the app

```bash
streamlit run roots_and_drift_app.py
```

The app will open in your browser automatically, usually at `http://localhost:8501`.

---

## How to Run the Simulation

1. **Setup screen:** Fill in the origin country, origin city, heritage language, destination country, and destination city. Then adjust the seven sociological variable sliders. Click Run Simulation.

2. **Geographic research:** The system silently analyzes the diaspora community context for the destination city. This takes a few seconds.

3. **Profile Agent (Chapter 1):** The first agent builds a cultural baseline from your inputs. You will see starting scores for four dimensions, resilience anchors, risk factors, and a narrative paragraph. The MR score (composite cultural preservation score) appears for the first time here.

4. **Drift Stages 1 and 2 (Chapters 2 and 3):** The simulation runs Arrival and Adolescence automatically. After each stage the chart updates and a new narrative appears describing what shifted and why.

5. **The Pivot (Chapter 4):** The simulation pauses at age 18. You will see the current MR score and the trajectory so far. Choose one of four life paths to continue. This choice affects what the model reasons about in the remaining stages.

6. **Drift Stages 3 and 4 (Chapters 5 and 6):** The simulation resumes with your pivot factored in and runs Early Adulthood and Established Life.

7. **Final Report (Chapter 7):** The Reflection Agent produces a tabbed report covering the narrative summary, turning points and top drivers, counterfactuals, and the full JSON state store. You can use the Restart button in the sidebar to run a new simulation.

---

## Project Structure

```
roots_and_drift_app.py    Main Streamlit application
requirements.txt          Python dependencies
.env                      Your API keys (you create this, not included)
.env.example              Template showing what the .env file should look like
README.md                 This file
```

---

## The Three Agents

| Agent | Persona | What It Does |
|---|---|---|
| Profile Agent | The Architect | Takes the 8 user variables and geographic context, builds a culturally grounded baseline with starting scores for all four dimensions |
| Drift Simulation Agent | The Simulator | Runs four times, once per life stage. Each run receives the actual output of the prior stage so drift compounds realistically rather than being predicted from the start |
| Reflection Agent | The Analyst | Receives the full trajectory and generates a synthesis report with ranked drivers, turning point analysis, and two counterfactual scenarios |

---

## The Four Cultural Dimensions

| Dimension | What It Measures |
|---|---|
| Language | Heritage language fluency and use frequency over time |
| Cultural Practice | Engagement with traditional food, customs, and celebrations |
| Social Affiliation | Composition of social circle (co-ethnic vs host-culture) |
| Self-Presentation | Name use, accent, cultural self-identification in public |

---

## MR Score

The MR (Magnitude of Retention) score is the composite cultural preservation score shown throughout the simulation.

**Formula:** MR = (Language + Cultural Practice + ((Social Affiliation + Self-Presentation) / 2)) / 3

**Thresholds:**
- 65 and above: Strong Preservation (shown in green)
- 40 to 64: Moderate Erosion (shown in amber)
- Below 40: Critical Erosion (shown in red)

---

## Evaluation Test Cases

If you want to reproduce the five evaluation scenarios from the Phase 2 report, here are the input configurations:

**TC-01 — The Late Arrival**
Age: 16, Anchor: 8, Language use: 7, Homophily: 5, Density: Low, No institutional anchor, Transmission: 6
Expected: Language score at age 25 at or above 60

**TC-02 — The Child Migrant**
Age: 9, Anchor: 3, Language use: 4, Homophily: 3, Density: Low, No institutional anchor, Transmission: 4
Expected: Language score at age 25 below 25

**TC-03 — The Institutional Buffer**
Run twice with Age: 12, Anchor: 5, Density: Low, all else equal. First run with institutional anchor ON, second with it OFF.
Expected: Cultural practice score at least 15 points higher in the ON run at Stage 4

**TC-04 — The Pivot Divergence**
Same baseline run twice. First pivot: Community Anchor. Second pivot: Professional Assimilation.
Expected: At least two dimensions diverge by 12 or more points by Stage 4

**TC-05 — Structural Inertia**
Age: 9, Anchor: 2, Language use: 2, Homophily: 2, Density: Very low, No institutional anchor, Transmission: 2. Use Community Anchor as pivot.
Expected: Final MR below 45 despite protective pivot

---

## Known Limitations

- The geographic community context is generated from the LLM's training knowledge. It is generally accurate for large, well-documented diaspora communities but may be less specific for smaller or less-represented groups.
- The simulation models population-level patterns, not individual predictions. A specific real person's experience may differ significantly from what the simulation produces.
- All session data is stored in Streamlit session state and cleared when the browser session ends. Nothing is persisted between runs.
- API calls send user inputs (city names, language, variable values) to Groq or OpenAI under their standard API terms. No personally identifiable information is required to run the simulation.

---

## Troubleshooting

**The app says no API keys were found**
Make sure your `.env` file is in the same folder as `roots_and_drift_app.py` and that the key names are spelled exactly as `GROQ_API_KEY` and `OPENAI_API_KEY`.

**An agent returned invalid JSON**
This occasionally happens when the LLM produces a response that does not parse correctly. Click Restart in the sidebar and try again. If it happens consistently, try switching to a different pivot choice or slightly different variable values.

**The app is slow between stages**
Each stage makes a separate API call. Groq is generally very fast (under 3 seconds per stage). If OpenAI is being used as fallback it may take slightly longer.

**Streamlit version errors**
Make sure you are running Python 3.9 or higher and that you installed from the requirements.txt file rather than installing packages individually.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| streamlit | 1.32.0+ | Frontend and session state management |
| plotly | 5.19.0+ | Interactive trajectory chart |
| openai | 1.12.0+ | Unified client for Groq and OpenAI API calls |
| python-dotenv | 1.0.0+ | Loading API keys from .env file |
