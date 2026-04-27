# AI Usage Disclosure
**Project:** Cultural Preservation Simulation Agent
**Author:** Iteoluwa Ibitoye | Agentic Technologies, Spring 2026
**Tool used:** Claude (Anthropic), claude.ai, Claude Sonnet, Spring 2026

---

## Overview

Claude was used throughout all three phases of this project as a thinking partner, coding assistant, and drafting aid. This document covers the key interactions, what was accepted from AI output, what was revised, and what was independently verified or developed by the author. The final simulation, evaluation plan, and written materials reflect the author's own design decisions made through an iterative conversation rather than wholesale adoption of generated output.

---

## Phase 1 Interactions

### Interaction 1 — Problem framing and system boundary

**Prompt given:** A description of the simulation concept around cultural preservation among first-generation immigrants, with a question about what system boundary and market context to use.

**What Claude produced:** An initial suggestion to use a mid-size US city as the system boundary.

**What was accepted:** The general framing of the problem as a path-dependent dynamic system.

**What was rejected:** The mid-size city suggestion. The author independently developed a more specific and compelling context: the professional services labor market in a tech-driven metropolitan area, focused on entry-to-mid-level white-collar roles. This decision was made by the author and is noted explicitly in the Phase 2 AI appendix.

---

### Interaction 2 — Variable selection and loop design

**Prompt given:** A list of variables the author wanted to work with, with a request for feedback.

**What Claude produced:** Feedback on the variable list, a recommendation to add Unemployment Duration as a 12th variable to close the B1 loop, and an initial causal loop structure.

**What was accepted:** The recommendation to add Unemployment Duration. The loop structure was used as a starting point.

**What was revised:** Job Security to Unemployment Duration polarity was changed from (+) to (−) by the author after reviewing the logic. Claude had labeled it incorrectly.

**What was independently verified:** The author reviewed every causal link in the diagram and confirmed each polarity before finalizing.

---

### Interaction 3 — Agent canvas design

**Prompt given:** A request to complete the three agent canvases (Profile Agent, Drift Simulation Agent, Reflection Agent).

**What Claude produced:** Full agent canvas drafts including inputs, outputs, key behaviors, and failure modes.

**What was accepted:** The Re-awakening Trigger (allowing scores to rise in Early Adulthood when institutional anchors are present), the Volatility Instruction, and the Resilience Anchors concept.

**What was revised:** The author added the Cultural Biography field and personal_anchor_used JSON field independently, which Claude had not proposed.

---

## Phase 2 Interactions

### Interaction 4 — Architecture justification

**Prompt given:** A description of the simulation concept and a question about whether a multi-agent system was actually necessary or whether a single LLM call could do the same thing.

**What Claude produced:** Four justifications for multi-agent design centered on the human-in-the-loop pause mechanic, path dependency compounding, independent auditability, and the qualitative difference between the Drift Agent and Reflection Agent reasoning tasks.

**What was accepted:** The four-part justification framework, which became the basis for the architecture rationale in the Phase 2 and Phase 3 reports.

**What was verified independently:** The author confirmed that a single-prompt system genuinely cannot pause mid-generation for a real human choice, which validated the strongest justification.

---

### Interaction 5 — Streamlit prototype construction

**Prompt given:** Early Streamlit code was shared alongside a request to fix a broken Gemini API call returning 404 errors and to rebuild using a more reliable provider.

**What Claude produced:** A diagnosis that the google-generativeai package was deprecated, a recommendation to switch to Groq with OpenAI as fallback, and a full rewrite of the call_llm function using the OpenAI-compatible interface.

**What was accepted:** The Groq-first, OpenAI-fallback architecture (later reversed to OpenAI primary based on author testing). The .env file approach for API key management. The json_mode parameter design.

**What was revised:** The author switched provider priority from Groq-primary to OpenAI-primary after observing that GPT-4o Mini produced more consistent JSON adherence during development testing. The author also removed the geographic research visible stage and made it run silently in the background — Claude had built it as a separate screen the user had to click through.

---

### Interaction 6 — Geographic grounding feature

**Prompt given:** A question about whether adding origin city, destination city, and heritage language would make the simulation more story-like and grounded, and whether live web search could be used.

**What Claude produced:** Two options — live Gemini web search grounding, or LLM training knowledge with a well-structured geographic research prompt. After live search repeatedly failed due to API version issues, Claude recommended switching to training knowledge.

**What was accepted:** The geographic research prompt structure. The two-stage approach (plain text narrative plus structured JSON).

**What was revised:** The author independently decided which fields to add to the setup screen and decided to add heritage language as a separate field rather than bundling it into origin country, based on the project's focus on language as a distinct cultural dimension.

---

### Interaction 7 — Multi-choice stage decisions

**Prompt given:** A request to replace the single pivot with richer stage-specific choice sets.

**What Claude produced:** An initial draft of the choice mechanic with scaling rules (100/70/50 percent for 1/2/3 choices).

**What was revised significantly:** All 24 individual choice cards (8 per stage) were written by the author based on their own knowledge of real immigrant experiences. Claude drafted the mechanic structure; the author wrote every specific choice label, description, and score delta. The "Stinky Lunch Moment," "The Accent Filter," "The Saturday School Sentence," and all other named choices are the author's own framing.

**What was independently verified:** Score deltas for each choice were reviewed by the author to confirm they were sociologically directionally correct before implementation.

---

### Interaction 8 — Narrative quality improvement

**Prompt given:** A sample narrative output was shared with the observation that it read like a travel brochure ("vibrant Nigerian community," "52nd Street corridor") rather than a personal experience.

**What Claude produced:** A diagnosis of the root cause (LLM pattern-matching on cultural group) and two proposed fixes: a banned word list and a specificity requirement.

**What was accepted:** The banned word list concept and the personal biography field approach.

**What was independently implemented:** The author wrote the complete list of banned words based on their own observation of which words appeared most generically in outputs. The author also designed the cultural biography prompt text on the setup screen.

---

### Interaction 9 — Report writing (Phase 2 and Phase 3)

**Prompt given:** Requests to draft the Phase 2 and Phase 3 written reports in a natural grad-student voice, avoiding overly technical language and em-dashes.

**What Claude produced:** Draft text for all report sections.

**What was accepted:** The overall structure and most of the analytical prose as a strong starting draft.

**What was revised:** The author reviewed every section of both reports. The individual reflection section in Phase 3 was reviewed carefully to ensure it accurately reflected the author's own experience and learning rather than a generic student voice. Several sections were shortened and reworded to match the author's natural register. All numeric values in the evaluation results table were filled in by the author from actual test run data.

**What was independently written:** The problem statement framing drawing on the author's own family experience (cousins who moved younger, the accent shifts, the name changes) was the author's own observation. Claude shaped the language; the content and specificity came from the author.

---

### Interaction 10 — Evaluation plan design

**Prompt given:** A request to design the full evaluation plan with test cases that go beyond happy-path demos.

**What Claude produced:** Five initial test cases with hypotheses, input profiles, and numeric thresholds.

**What was accepted:** The controlled comparison methodology for TC-03 and TC-04 (running the simulation twice with one variable changed).

**What was expanded by the author:** The author added TC-06 (cross-cultural validity), TC-07 (personalisation fidelity), TC-08 (counterfactual specificity), TC-09 (tipping-point detection), and TC-10 (sensory threading) independently. The 5-point counterfactual specificity rubric for TC-08 was designed entirely by the author.

**What was revised:** TC-01 success threshold was lowered from 65 to 60 by the author to account for the low neighborhood density condition at late arrival age.

---

## What Was Not Used from AI Output

- The author rejected an early suggestion to model the simulation as a causal loop diagram assignment (the non-coding track). The author chose the coding track and built a functioning simulation.
- The author rejected Claude's initial mid-size city system boundary in favor of a more specific professional services context.
- All 24 stage-specific choice cards are the author's original content, not AI-generated.
- The evaluate.py automated evaluation script was written by the author with general guidance on structure from Claude.

---

## Independent Verification Performed

- All agent prompts were tested locally and revised based on actual output before being considered final
- All score deltas in the choice sets were reviewed for directional plausibility by the author
- All geographic validation logic was tested with intentionally wrong inputs (e.g., Lagos, USA) before submission
- All evaluation results in the final report were filled in from actual test run data, not estimated
- The final version of the app was run end-to-end at least five times by the author before submission to verify stability
