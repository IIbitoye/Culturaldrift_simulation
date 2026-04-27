# Evaluation & Trace Artifacts – Cultural Preservation Simulation

## 1. Evaluation Results (CSV equivalent)

| case_id | case_type | input_or_scenario | expected_behavior | actual_behavior | outcome | evidence_or_citation | notes |
|---------|-----------|-------------------|-------------------|------------------|---------|----------------------|-------|
| TC-01 | single | Age 16, Anchor 8, Density Low | Language ≥ 60 at Stage 4 | Language = 70 | PASS | `TC-01_trace.json`, final language 70 | Late arrival protects language as hypothesised |
| TC-02 | single | Age 9, Anchor 3, Density Low | Language < 25 at Stage 4 | Language = 15 | PASS | `TC-02_trace.json`, final language 15 | Child migrant shows expected erosion |
| TC-03 | paired | Institutional anchor absent vs. present | Cultural Practice Δ ≥ 15 | Δ = 10 | FAIL | `TC-03_trace.json`, CP no anchor=45, with anchor=55 | Anchor effect exists but weaker than threshold |
| TC-04 | paired | Community pivot vs. Career pivot | ≥2 dimensions Δ ≥ 12 | SA Δ=37, CP Δ=22, L Δ=15 | PASS | `TC-04_trace.json`, deltas recorded | Strong divergence confirms choice sensitivity |
| TC-05 | single | Age 5, all protective vars min | Final MR < 45, pivot impact < 8 | MR=8.3, impact=1.3 | PASS | `TC-05_trace.json`, final MR 8.3 | Structural inertia correctly prevents recovery |
| TC-06 | paired | Nigerian/Yoruba vs. Mexican/Spanish in Houston | ≥2 dimensions Δ ≥ 10 | Only self‑presentation Δ=15 | FAIL | `TC-06_trace.json`, language Δ=5, practice Δ=5 | Cross‑cultural distinction weak; LLM training bias |
| TC-07 | paired | Generic vs. vivid biography | MR Δ ≥ 8 | MR Δ = 8.3 | PASS | `TC-07_trace.json`, generic MR=62, vivid MR=70.3 | Biography improves MR as expected |
| TC-08 | single | Standard baseline | Counterfactual specificity score ≥ 4/5 | Score = 2/5 | FAIL | `TC-08_trace.json`, counterfactual texts | Vague references, missing numeric estimates |
| TC-09 | single | Choices causing >15 drop | Tipping point detected | Detected = True | PASS | `TC-09_trace.json`, warning in UI | Volatility warning surfaced correctly |
| TC-10 | single | Vivid biography with "egusi" | Keyword appears in ≥2 stages | Keyword count = 0 | FAIL | `TC-10_trace.json`, narrative texts | Biography threading failed; no sensory anchor used |
| TC-11 | single | Late Arrival (London) | Language ≥ 60 | Language = 68 | PASS | `TC-11_trace.json` | Destination variance works in this case |
| TC-12 | single | Child Migrant (Toronto) | Language < 25 | Language = 22 | PASS | `TC-12_trace.json` | Destination variance works |
| adversarial‑1 | single | All sliders max, empty bio | No unrealistic score inflation | MR = 92 | PASS | run log, final MR 92 | Scores high but plausible given extreme settings |
| adversarial‑2 | single | Contradictory bio: "I hate my culture" | Starting anchors lowered | Anchor used=1, starting SA=32 | PASS | profile agent JSON | Profile Agent respects negative anchor |
| adversarial‑3 | single | Nonsense input: "asdf", "xyz" | Geographic validation error | Red error, stop | PASS | screenshot geo_validation_error.png | Quick validation catches nonsense |

## 2. Failure Log

| failure_id | date | version_tested | what_triggered_the_problem | what_happened | severity | fix_attempted | current_status |
|------------|------|----------------|----------------------------|---------------|----------|----------------|----------------|
| F‑01 | 2025-04-10 | v0.1 | No volatility instruction | Scores dropped smoothly (5 pts per stage) across all stages – “hallucinated linearity” | High | Added “Volatility Instruction” and 15‑point tipping point rule | Fixed – TC‑09 confirmed detection |
| F‑02 | 2025-04-12 | v0.2 | Empty biography field | LLM invented “cooking egusi soup on Sundays” as default anchor | Medium | Allowed empty anchor; prompt instructs “do not invent” | Fixed – empty bio now produces neutral narrative |
| F‑03 | 2025-04-15 | v0.3 | User toggling checkboxes repeatedly | Scores kept dropping with each toggle (cumulative delta) | High | Introduced stage‑baseline score; recompute deltas from baseline | Fixed – toggling no longer drifts scores |
| F‑04 | 2025-04-18 | v0.4 | Missing geo validation | User entered “New York, Nigeria” – simulation ran nonsense research | Critical | Added `quick_geo_validation` LLM call before geo research | Fixed – validation error stops simulation |
| F‑05 | 2025-04-20 | v0.5 | LLM invented restaurants / cultural centres | Geographic research returned fake names like “Suya Palace” | Medium | Prompt: “Do NOT make up names; use null or empty list” | Partial – still possible for obscure diaspora groups |
| F‑06 | 2025-04-22 | v0.6 | Only one pivot at age 18 | Trajectories felt generic, not personalised | High | Added multi‑choice checkboxes (max 3) at each drift stage | Fixed – TC‑04 shows strong divergence |
| F‑07 | 2025-04-25 | v0.7 | TC‑10 evaluation | Keywords from biography never appeared in narratives | High | Not yet fixed – future: post‑generation keyword check + re‑prompt | Open – documented as limitation |
| F‑08 | 2025-04-26 | v0.8 | TC‑06 evaluation | Nigerian and Mexican trajectories nearly identical | Medium | Added requirement for origin‑specific institutions in geo prompt | Open – requires retrieval‑augmented generation |

## 3. AI Usage Log

| Tool name and version | What you used it for | Exact prompt or task given to the tool | What you changed manually afterward | What you verified independently |
|-----------------------|----------------------|------------------------------------------|-------------------------------------|--------------------------------|
| Claude (Anthropic), version 2025-01-01 | Drafting Streamlit prototype code | “Fix broken call_gemini function and rebuild app using Groq with OpenAI fallback” | Removed geographic research from visible UI to silent background; adjusted pivot card layout | Ran simulation with multiple configurations; verified API calls work |
| Claude (Anthropic) | Designing agent prompts (Profile, Drift, Reflection) | “Write a prompt for the Profile Agent that takes 8 variables and geographic context, outputs baseline scores and narrative” | Added banned‑word lists, volatility instruction, personalisation rule | Tested with extreme inputs to ensure JSON output; evaluated with TC‑01…TC‑10 |
| Claude (Anthropic) | Generating choice sets for life stages | “Create 8 realistic choices for Adolescence, Early Adulthood, and Established Life with score deltas” | Adjusted delta values (scaled to 100%/70%/50%); removed unrealistic options | Manually reviewed each choice for cultural relevance; tested in UI |
| Claude (Anthropic) | Building evaluation script | “Write evaluate.py that runs test cases and produces CSV summary” | Added LLM judge for counterfactual specificity (TC‑08); added error handling for TC‑11/TC‑12 | Ran full evaluation; compared outputs with manual inspection |
| Claude (Anthropic) | Refactoring to simulation_core.py | “Separate core logic from Streamlit UI so evaluate.py can import functions” | Moved all prompts and run_full_simulation into core; fixed import errors | Verified both Streamlit app and evaluation script run independently |
| Human (author) | Geographic research prompt details | N/A | Added requirement for “name at least one specific institution” and banned “vibrant” | Checked geo outputs for Houston, London, Toronto – real institutions appear |
| Human (author) | Thresholds for test cases | N/A | Set TC‑01 language ≥60, TC‑02 <25, TC‑03 Δ≥15, etc. | Based on Phase 2 design; no external validation (documented limitation) |

---

**Note:** All trace JSON files (`TC-*_trace.json`) are included in the supplementary materials folder. The full `evaluation_results.csv` is also provided.