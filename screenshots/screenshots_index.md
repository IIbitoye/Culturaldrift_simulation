# Screenshot Index – Cultural Preservation Simulation

This index documents the UI and workflow of the Cultural Preservation Simulation, highlighting agent coordination, human‑in‑the‑loop pause points, governance mechanisms, and evaluation artifacts.

| Screenshot File | Category | What it Shows | Why it Matters | Where Discussed |
|----------------|----------|---------------|----------------|-----------------|
| `01_Landing_Screen.png` | Home / Landing | The initial configuration screen: origin/destination inputs, heritage language field, and optional “Cultural Biography” memory box. | Shows the user’s first interaction – setting the migration context and personal anchor. | Section 3 (Implementation) |
| `02_Initial_Settings_and_controls.png` | Settings / Controls | Detailed view of the eight sociological variable sliders: Age at migration, Cultural anchor, Language use, Homophily, Density, Institutional toggle, Transmission pressure. | Demonstrates the input variables that calibrate the Profile Agent’s baseline scores. | Section 3 (Implementation) |
| `07-Evidence_Source_View.png` | Evidence / Source | The Geographic Research stage – analytical prose about the Nigerian diaspora in Pittsburgh (real neighbourhoods, institutions, cultural distance). | Proves the “Architect” agent grounds the simulation in real‑world sociological context, preventing generic “hallucinated” drift. | Section 3 (Implementation – Geographic research) |
| `04_User_Workflow.png` | Main Interaction | A multi‑select checkbox interface during the Adolescence stage (human‑in‑the‑loop pause). User can pick up to three life choices (e.g., “Digital Diaspora”, “Cultural Youth Group”). | Shows the coordination logic where the pipeline pauses to allow user agency to steer the identity trajectory. | Section 2 (Architecture) |
| `03_User_Workflow.jpg` | Failure / Boundary | An active drift stage with a red “Tipping point detected” warning. This occurs when a dimension score drops >15 points in one stage. | Evidence of escalation behaviour (Volatility Warning) as required by Phase 2 feedback. | Section 7 (Governance) |
| `10-Failure_Boundary_Case.png` | Failure / Boundary | Automated geographic plausibility check failure – red error message when user enters an impossible pair (e.g., “Germany, Nigeria”). | Demonstrates input validation; stops the simulation from running nonsense research. | Section 7 (Governance), Section 6 (Failure Analysis 6.2) |
| `06-Evaluation_and_Results.png` | Evaluation / Results | Final Reflection Agent report: Magnitude of Retention (MR) score (54.8/100), verdict (“Moderate Erosion”), and multi‑dimensional trajectory chart. | Shows final artifact quality and the successful synthesis of all four cultural dimensions by the Reflection Agent. | Section 5 (Results) |
| `08-Export_Artifact_Screen.png` | Artifact / Export | The final stage of the report with a “Download run log (JSON)” button and the complete JSON state store expander. | Allows users to export full run logs for offline evaluation – core to the evaluation package requirement. | Section 3 (Implementation – Export) |
| `09-Saved_thread_and_history.jpg` | State / History View | The “Agent Handoff Traces” expander in the sidebar, listing individual JSON snapshots (after_profile_agent, after_choices_Adolescence, etc.) and a download button for all handoffs. | Proves transparency and agent coordination through captured JSON traces – moves the project from “design” to “working system”. | Section 2 (Architecture, State management) |
| `05_Artifacts_and_json_traces.jpg` | State / History View | Alternative view of the JSON state store inside the final report (Research & Data tab) with the full trajectory data. | Shows the raw data behind the narratives, ensuring auditability. | Section 2 & Section 7 (Governance) |

## Mapping to Submission Requirements

| Requirement | Provided by Screenshot | Description |
|-------------|------------------------|-------------|
| Home / Landing screen | `01_Landing_Screen.png` | Setup screen with origin/destination and biography. |
| Main interaction screen | `04_User_Workflow.png` | Multi‑choice pause during adolescence. |
| Evidence / citation / source view | `07-Evidence_Source_View.png` | Geographic research with real diaspora data. |
| Saved thread / history / state view | `09-Saved_thread_and_history.jpg`, `05_Artifacts_and_json_traces.jpg` | JSON handoff snapshots and state store. |
| Artifact generation or export screen | `08-Export_Artifact_Screen.png` | Download run log button. |
| Evaluation or results screen | `06-Evaluation_and_Results.png` | Final MR score, chart, verdict. |
| Failure case or boundary case | `03_User_Workflow.jpg` (tipping point), `10-Failure_Boundary_Case.png` (geo validation) | Two distinct failure examples. |
| Settings, controls, or filters | `02_Initial_Settings_and_controls.png` | Eight sociological variable sliders. |

All screenshots referenced are located in the `/screenshots` folder of the submission package.