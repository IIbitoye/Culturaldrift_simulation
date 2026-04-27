# Version Notes — Cultural Preservation Simulation Agent
**Project:** Cultural Preservation Simulation Agent
**Author:** Iteoluwa Ibitoye | Agentic Technologies, Spring 2026

---

## v1.0 — Initial Prototype (Phase 2)

**What was built:**
- Three-agent sequential pipeline: Profile Agent, Drift Simulation Agent, Reflection Agent
- Single pivot choice at age 18 (four options)
- Basic Streamlit interface with dark theme
- Groq Llama 3.3 70B as primary LLM
- JSON state passing between agents
- Plotly trajectory chart

**Known issues at this version:**
- Narratives defaulted to generic cultural tropes ("vibrant community," "strong sense of belonging")
- Single pivot felt like a menu click rather than a meaningful decision
- No geographic plausibility validation
- No run log export
- No stage-specific user choices beyond one pivot
- Tipping point log triggered inconsistently

---

## v1.1 — Narrative Quality Fix

**What changed:**
- Added banned word list to all agent prompts (vibrant, rich culture, cultural tapestry, bustling, beloved, cultural scene)
- Added volatility instruction to Drift Agent: required sharp drops to have a named triggering event
- Added personal biography field on setup screen
- Profile Agent now extracts personal_anchor_used and stores in JSON state
- Drift Agent instructed to reference the specific anchor detail rather than generic cultural tropes

**Test result:** TC-07 (personalisation fidelity) now passes. TC-10 (sensory threading) still fails — anchor is extracted but not reliably carried across all narrative stages.

---

## v1.2 — Geography and Validation

**What changed:**
- Added quick_geo_validation LLM call before geographic research runs
- Validates city/country pair and heritage language plausibility
- Implausible pairs (e.g., New York, Nigeria) produce an error with a correction prompt
- Geographic research now produces both a plain-text narrative and a structured JSON (restaurants, institutions, neighborhoods, cultural distance, assimilation pressure)
- Structured JSON displayed in Research and Data tab of final report

**Test result:** Geographic validation correctly catches intentional wrong pairs. TC-06 (cross-cultural validity) still fails — structured output produces similar institutional descriptions for different origin groups in the same destination city.

---

## v1.3 — Multi-Choice Stage Decisions

**What changed:**
- Replaced single pivot at age 18 with stage-specific multi-choice checkbox sets
- 8 choices available per stage (Adolescence, Early Adulthood, Established Life)
- Maximum 3 choices selectable per stage
- Score deltas scale: 100% for 1 choice, 70% for 2 choices, 50% for 3 choices
- Choices recorded in JSON state and referenced by name in next stage narrative
- Stage baseline stored to prevent score drift on checkbox toggling

**Issue discovered:** Score drift bug — checking and unchecking choices repeatedly caused scores to accumulate incorrectly because deltas were applied to running totals rather than to a fixed stage baseline.

**Fix:** Introduced baseline_key per stage. Deltas are recomputed from the baseline based on current selection state, not applied incrementally.

**Test result:** TC-04 (pivot divergence) now produces large deltas (SA Δ = 37, CP Δ = 22), confirming the simulation is highly sensitive to multi-stage choices.

---

## v1.4 — Evidence and Logging

**What changed:**
- Added state snapshot system: record_snapshot() called at every agent handoff
- Snapshots downloadable individually or as a combined file from Agent Handoff Traces panel in sidebar
- Added JSON run log export button at end of each simulation
- Run log includes all agent outputs, scores, narratives, failure log entries, and provider metadata
- Timestamp and case label auto-generated in filename

**Purpose:** Enables evaluation evidence collection without manual copying from the UI.

---

## v1.5 — LLM Provider Switch and Tipping Point Fixes

**What changed:**
- Switched primary LLM from Groq to OpenAI GPT-4o Mini
- Groq Llama 3.3 70B retained as fallback
- Fixed tipping point log: prompt updated to explicitly compare new scores against prior stage scores (not original baseline)
- Added defensive Python check: if any dimension drops more than 15 points and the agent did not log it, the code logs it automatically
- Added tipping_point_occurred flag to JSON state
- Reflection Agent receives this flag and is instructed to prioritize the tipping point event in its ranked drivers and turning point analysis
- Added critical erosion warning (MR < 20) with three options: continue, go back and choose differently, or end simulation early

**Test result:** TC-09 (tipping point detection) now passes consistently across all three runs.

---

## v1.6 — Final Submission Version

**What changed:**
- Automated evaluation script (evaluate.py) built to run all 10 test cases programmatically
- Each test case run three times, modal outcome reported
- evaluate.py uses same agent functions as the Streamlit UI to ensure consistency
- LLM judge added to evaluate counterfactual specificity (TC-08)
- Final UI cleanup: progress bar, chapter-based progression labels, sidebar live MR score
- README, AI_USAGE.md, and version_notes.md finalized

**Known open issues at final submission:**
- TC-03 (institutional buffer): delta of 10 points, below 15-point threshold. Root cause is variable interaction complexity — the institutional anchor competes with neighborhood density in the agent's reasoning. Documented as an open limitation.
- TC-06 (cross-cultural validity): LLM training data coverage is uneven across diaspora groups. Requires retrieval-augmented generation with real-world institutional databases to fix properly.
- TC-08 (counterfactual specificity): Reflection Agent scores 2/5. Few-shot examples added to prompt did not fully resolve the issue. Documented as future work.
- TC-10 (sensory threading): Keywords extracted by Profile Agent do not consistently appear in later stage narratives. Post-generation keyword check proposed for future version.

---

## Open Issues for Future Work

| Priority | Issue | Proposed Fix |
|---|---|---|
| High | Cross-cultural overgeneralization (TC-06) | Integrate Google Places API or Wikidata for real-time institutional data |
| High | Sensory keyword threading (TC-10) | Add post-generation check that re-prompts if keywords are missing |
| Medium | Counterfactual vagueness (TC-08) | Few-shot examples with specific numeric estimates in Reflection Agent prompt |
| Medium | Institutional buffer effect (TC-03) | Increase weight of institutional anchor variable in Profile Agent calibration |
| Low | No empirical score calibration | Ground thresholds against NHLRC corpus or Portes and Rumbaut CILS data |
| Low | Session-based only | Add persistent storage for cross-session trajectory comparison |
