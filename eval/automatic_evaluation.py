import json
import time
import csv
import re
from simulation_core import run_full_simulation, compute_mr, call_llm

# ------------------------------------------------------------
# HELPER FUNCTIONS FOR EVALUATION METRICS
# ------------------------------------------------------------
def evaluate_counterfactual_specificity(reflection: dict) -> int:
    """Score 1-5 based on counterfactual quality for TC-08."""
    cf_a = reflection.get("counterfactual_a", "")
    cf_b = reflection.get("counterfactual_b", "")
    score = 0
    for cf in [cf_a, cf_b]:
        has_city = any(city in cf.lower() for city in ["houston", "atlanta", "chicago", "dallas", "austin", "philadelphia", "columbus"])
        has_numeric = any(c.isdigit() for c in cf) and ("mr" in cf.lower() or "point" in cf.lower())
        has_causal = any(phrase in cf.lower() for phrase in ["because", "due to", "since", "would have", "could have"])
        if has_city and has_numeric and has_causal:
            score += 2
        elif has_city and has_numeric:
            score += 1
        elif has_city:
            score += 0.5
    return min(5, score)

def check_tipping_point_detection(state: dict, reflection: dict, trajectory: list) -> bool:
    if state.get("tipping_point_occurred"):
        return True
    turning = reflection.get("turning_point", "").lower()
    if any(phrase in turning for phrase in ["drop", "tipping", "sharp", "plummeted", "fell", "loss"]):
        return True
    for i in range(1, len(trajectory)):
        prev = trajectory[i-1]["scores"]
        curr = trajectory[i]["scores"]
        for dim in ["language", "cultural_practice", "social_affiliation", "self_presentation"]:
            if prev.get(dim, 50) - curr.get(dim, 50) > 15:
                return True
    return False

def count_sensory_keywords(trajectory: list, biography: str) -> int:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', biography.lower())
    stopwords = {"and", "the", "of", "to", "in", "that", "is", "was", "for", "on", "with", "are", "as", "by", "this", "my", "her", "his", "their"}
    keywords = [w for w in words if w not in stopwords and len(w) >= 4]
    if not keywords:
        keywords = ["egusi", "fela", "accent", "soup", "kitchen", "sunday"]
    count = 0
    for stage in trajectory:
        narrative = stage.get("narrative", "").lower()
        if any(kw in narrative for kw in keywords):
            count += 1
    return count

def generate_llm_explanation(test_id: str, outcome: str, metrics: dict, expected: str, trace_summary: str = "") -> str:
    """Call LLM to produce a one‑sentence explanation of the test result."""
    prompt = f"""You are an evaluation analyst. Write ONE short sentence (max 25 words) explaining why the following test case {outcome}ed.

Test ID: {test_id}
Outcome: {outcome}
Metrics: {json.dumps(metrics)}
Expected condition: {expected}
Brief trace: {trace_summary[:500]}

Return only the sentence, no extra text.
"""
    response, _ = call_llm(prompt, json_mode=False)
    return response.strip().replace('"', "'")

# ------------------------------------------------------------
# MAIN EVALUATION FUNCTION
# ------------------------------------------------------------
def evaluate():
    # Expected conditions for each test case (used in CSV and LLM prompt)
    expected_conditions = {
        "TC-01": "final language >= 60",
        "TC-02": "final language < 25",
        "TC-05": "final MR < 45 and pivot impact < 8",
        "TC-08": "counterfactual specificity score >= 4",
        "TC-09": "tipping point detected == True",
        "TC-10": "sensory keyword count >= 2",
        "TC-11": "final language >= 60 (London destination)",
        "TC-12": "final language < 25 (Toronto destination)",
        "TC-03": "cultural practice delta >= 15",
        "TC-04": "two dimensions delta >= 12",
        "TC-06": "two dimensions delta >= 10 (cross‑cultural)",
        "TC-07": "MR delta (vivid - generic) >= 8"
    }

    results = {}          # for internal storage
    csv_rows = []         # for CSV output

    # -----------------------------------------------------------------
    # SINGLE TEST CASES (TC-01, TC-02, TC-05, TC-08, TC-09, TC-10, TC-11, TC-12)
    # -----------------------------------------------------------------
    single_cases = ["TC-01", "TC-02", "TC-05", "TC-08", "TC-09", "TC-10", "TC-11", "TC-12"]
    # Define configurations for TC-11 and TC-12 (London/Toronto)
    extra_configs = {
        "TC-11": {
            "origin_country": "Nigeria", "origin_city": "Lagos",
            "dest_country": "UK", "dest_city": "London",
            "language": "Yoruba", "age": 16, "anchor": 8,
            "language_use": 7, "homophily": 5, "density": "Low",
            "institutional": False, "transmission": 3, "biography": ""
        },
        "TC-12": {
            "origin_country": "Nigeria", "origin_city": "Lagos",
            "dest_country": "Canada", "dest_city": "Toronto",
            "language": "Yoruba", "age": 9, "anchor": 3,
            "language_use": 3, "homophily": 2, "density": "Low",
            "institutional": False, "transmission": 2, "biography": ""
        }
    }

    for tc_id in single_cases:
        print(f"\nRunning {tc_id}...")
        # Get config and forced_choices (defined in the script below)
        if tc_id in ["TC-11", "TC-12"]:
            cfg = extra_configs[tc_id].copy()
            force = {}
        else:
            # You must define the TEST_CASES dictionary for the other singles.
            # For brevity, I'll inline the configs here (same as before).
            if tc_id == "TC-01":
                cfg = {
                    "origin_country": "Nigeria", "origin_city": "Lagos",
                    "dest_country": "USA", "dest_city": "Houston",
                    "language": "Yoruba", "age": 16, "anchor": 8,
                    "language_use": 7, "homophily": 5, "density": "Low",
                    "institutional": False, "transmission": 3, "biography": ""
                }
                force = {}
            elif tc_id == "TC-02":
                cfg = {
                    "origin_country": "Nigeria", "origin_city": "Lagos",
                    "dest_country": "USA", "dest_city": "Houston",
                    "language": "Yoruba", "age": 9, "anchor": 3,
                    "language_use": 3, "homophily": 2, "density": "Low",
                    "institutional": False, "transmission": 2, "biography": ""
                }
                force = {}
            elif tc_id == "TC-05":
                cfg = {
                    "origin_country": "Nigeria", "origin_city": "Lagos",
                    "dest_country": "USA", "dest_city": "Houston",
                    "language": "Yoruba", "age": 5, "anchor": 1,
                    "language_use": 1, "homophily": 1, "density": "Very low",
                    "institutional": False, "transmission": 1, "biography": ""
                }
                force = {
                    "Adolescence": ["Cultural Youth Group"],
                    "Early Adulthood": ["Heritage Travel"],
                    "Established Life": ["Only Yoruba at Home"]
                }
            elif tc_id == "TC-08":
                cfg = {
                    "origin_country": "Nigeria", "origin_city": "Lagos",
                    "dest_country": "USA", "dest_city": "Houston",
                    "language": "Yoruba", "age": 14, "anchor": 6,
                    "language_use": 6, "homophily": 5, "density": "Medium",
                    "institutional": False, "transmission": 5, "biography": ""
                }
                force = {
                    "Adolescence": ["Cultural Youth Group"],
                    "Early Adulthood": ["Heritage Travel"],
                    "Established Life": ["Only Yoruba at Home"]
                }
            elif tc_id == "TC-09":
                cfg = {
                    "origin_country": "Nigeria", "origin_city": "Lagos",
                    "dest_country": "USA", "dest_city": "Houston",
                    "language": "Yoruba", "age": 10, "anchor": 3,
                    "language_use": 3, "homophily": 2, "density": "Very low",
                    "institutional": False, "transmission": 2, "biography": ""
                }
                force = {
                    "Adolescence": ["The Accent Filter", "Refusing Traditional Dress"],
                    "Early Adulthood": ["Professional Code‑Switching"],
                    "Established Life": ["Complete Assimilation"]
                }
            elif tc_id == "TC-10":
                cfg = {
                    "origin_country": "Nigeria", "origin_city": "Lagos",
                    "dest_country": "USA", "dest_city": "Houston",
                    "language": "Yoruba", "age": 12, "anchor": 7,
                    "language_use": 7, "homophily": 6, "density": "Medium",
                    "institutional": True, "transmission": 6,
                    "biography": "Every Sunday my grandmother made egusi soup while my father played Fela Kuti. I am terrified of losing my Yoruba accent and the smell of her kitchen."
                }
                force = {
                    "Adolescence": ["The Saturday School Sentence"],
                    "Early Adulthood": ["The Kitchen Anchor"],
                    "Established Life": ["Only Yoruba at Home"]
                }
            else:
                continue

        try:
            state, ref, traj = run_full_simulation(cfg, force)
            # Compute metrics based on test case
            passed = False
            metrics = {}
            if tc_id == "TC-01":
                lang = state["scores"]["language"]
                passed = lang >= 60
                metrics = {"final_language": lang, "final_mr": compute_mr(state["scores"])}
                trace_summary = f"Final MR: {metrics['final_mr']}, Final Language: {lang}"
            elif tc_id == "TC-02":
                lang = state["scores"]["language"]
                passed = lang < 25
                metrics = {"final_language": lang}
                trace_summary = f"Final Language: {lang}"
            elif tc_id == "TC-05":
                mr = compute_mr(state["scores"])
                # baseline without pivot
                neutral_cfg = cfg.copy()
                neutral_state, _, _ = run_full_simulation(neutral_cfg, {})
                neutral_mr = compute_mr(neutral_state["scores"])
                pivot_impact = abs(neutral_mr - mr)
                passed = (mr < 45) and (pivot_impact < 8)
                metrics = {"final_mr": mr, "pivot_impact": pivot_impact}
                trace_summary = f"Final MR: {mr}, pivot impact: {pivot_impact}"
            elif tc_id == "TC-08":
                score = evaluate_counterfactual_specificity(ref)
                passed = score >= 4
                metrics = {"counterfactual_score": score}
                trace_summary = f"Score: {score}. CF A: {ref.get('counterfactual_a','')[:50]}, CF B: {ref.get('counterfactual_b','')[:50]}"
            elif tc_id == "TC-09":
                tip = check_tipping_point_detection(state, ref, traj)
                passed = tip
                metrics = {"tipping_point_detected": tip}
                trace_summary = f"Tipping detected: {tip}"
            elif tc_id == "TC-10":
                kw_count = count_sensory_keywords(traj, cfg["biography"])
                passed = kw_count >= 2
                metrics = {"sensory_keyword_count": kw_count}
                trace_summary = f"Keyword count: {kw_count}"
            elif tc_id in ["TC-11", "TC-12"]:
                lang = state["scores"]["language"]
                if tc_id == "TC-11":
                    passed = lang >= 60
                else:
                    passed = lang < 25
                metrics = {"final_language": lang}
                trace_summary = f"Final Language: {lang}"
            else:
                continue

            outcome = "PASS" if passed else "FAIL"
            # Generate LLM explanation
            explanation = generate_llm_explanation(tc_id, outcome, metrics, expected_conditions[tc_id], trace_summary)
        except Exception as e:
            print(f"⚠️ {tc_id} failed with error: {e}")
            outcome = "FAIL"
            metrics = {"error": str(e)}
            trace_summary = f"Simulation crashed: {e}"
            explanation = f"Simulation error: {e}. Could not complete test."
            passed = False

        # Store for later printing (optional)
        results[tc_id] = {"passed": passed, "metrics": metrics}
        # Build CSV row
        metric_value = ", ".join(f"{k}={v}" for k, v in metrics.items()) if metrics else "N/A"
        csv_rows.append({
            "case_id": tc_id,
            "case_type": "single",
            "name": tc_id,
            "outcome": outcome,
            "metric_value": metric_value,
            "expected": expected_conditions.get(tc_id, "see details"),
            "explanation": explanation
        })
        # Save trace JSON for these cases
        if 'state' in locals():
            with open(f"{tc_id}_trace.json", "w") as f:
                json.dump({"config": cfg, "forced_choices": force, "state": state, "reflection": ref, "trajectory": traj, "metrics": metrics}, f, indent=2)
        time.sleep(1)

    # -----------------------------------------------------------------
    # PAIRED TEST CASES (TC-03, TC-04, TC-06, TC-07)
    # -----------------------------------------------------------------
    # TC-03: Institutional Buffer
    print("\nRunning TC-03 (Institutional Buffer)...")
    cfg_A = {
        "origin_country": "Nigeria", "origin_city": "Lagos",
        "dest_country": "USA", "dest_city": "Houston",
        "language": "Yoruba", "age": 12, "anchor": 5,
        "language_use": 5, "homophily": 4, "density": "Low",
        "institutional": False, "transmission": 5, "biography": ""
    }
    cfg_B = cfg_A.copy()
    cfg_B["institutional"] = True
    try:
        state_A, _, _ = run_full_simulation(cfg_A, {})
        state_B, _, _ = run_full_simulation(cfg_B, {})
        cp_A = state_A["scores"]["cultural_practice"]
        cp_B = state_B["scores"]["cultural_practice"]
        delta = cp_B - cp_A
        passed = delta >= 15
        outcome = "PASS" if passed else "FAIL"
        metrics = {"delta": delta}
        trace_summary = f"Cultural Practice: without anchor={cp_A}, with anchor={cp_B}, delta={delta}"
        explanation = generate_llm_explanation("TC-03", outcome, metrics, expected_conditions["TC-03"], trace_summary)
        # Save trace
        with open("TC-03_trace.json", "w") as f:
            json.dump({"A": state_A, "B": state_B}, f, indent=2)
    except Exception as e:
        outcome = "FAIL"
        metrics = {"error": str(e)}
        trace_summary = f"Error: {e}"
        explanation = f"Simulation error: {e}"
        passed = False
    csv_rows.append({
        "case_id": "TC-03",
        "case_type": "paired",
        "name": "Institutional Buffer",
        "outcome": outcome,
        "metric_value": f"Δ CP = {metrics.get('delta', 'N/A')}",
        "expected": expected_conditions["TC-03"],
        "explanation": explanation
    })
    results["TC-03"] = {"passed": passed, "metrics": metrics}
    time.sleep(1)

    # TC-04: Pivot Divergence
    print("\nRunning TC-04 (Pivot Divergence)...")
    cfg_base = {
        "origin_country": "Nigeria", "origin_city": "Lagos",
        "dest_country": "USA", "dest_city": "Houston",
        "language": "Yoruba", "age": 14, "anchor": 6,
        "language_use": 5, "homophily": 5, "density": "Medium",
        "institutional": False, "transmission": 5, "biography": ""
    }
    force_A = {
        "Adolescence": ["Cultural Youth Group"],
        "Early Adulthood": ["Founding a Campus Org"],
        "Established Life": ["Cultural Mentorship"]
    }
    force_B = {
        "Adolescence": ["The Accent Filter"],
        "Early Adulthood": ["The Resume Name‑Change"],
        "Established Life": ["Complete Assimilation"]
    }
    try:
        state_A, _, _ = run_full_simulation(cfg_base, force_A)
        state_B, _, _ = run_full_simulation(cfg_base, force_B)
        dims = ["language", "cultural_practice", "social_affiliation", "self_presentation"]
        deltas = {d: abs(state_A["scores"][d] - state_B["scores"][d]) for d in dims}
        sorted_deltas = sorted(deltas.values(), reverse=True)
        passed = sorted_deltas[0] >= 12 and sorted_deltas[1] >= 12
        outcome = "PASS" if passed else "FAIL"
        metrics = deltas
        trace_summary = f"Deltas: {deltas}"
        explanation = generate_llm_explanation("TC-04", outcome, metrics, expected_conditions["TC-04"], trace_summary)
        with open("TC-04_trace.json", "w") as f:
            json.dump({"community_path": state_A, "assimilation_path": state_B}, f, indent=2)
    except Exception as e:
        outcome = "FAIL"
        metrics = {"error": str(e)}
        explanation = f"Simulation error: {e}"
        passed = False
    csv_rows.append({
        "case_id": "TC-04",
        "case_type": "paired",
        "name": "Pivot Divergence",
        "outcome": outcome,
        "metric_value": ", ".join(f"{k}={v}" for k, v in metrics.items() if k != "error"),
        "expected": expected_conditions["TC-04"],
        "explanation": explanation
    })
    results["TC-04"] = {"passed": passed, "metrics": metrics}
    time.sleep(1)

    # TC-06: Cross‑Cultural Validity
    print("\nRunning TC-06 (Cross‑Cultural Validity)...")
    cfg_NG = {
        "origin_country": "Nigeria", "origin_city": "Lagos", "dest_country": "USA", "dest_city": "Houston",
        "language": "Yoruba", "age": 12, "anchor": 5, "language_use": 5, "homophily": 5, "density": "Medium",
        "institutional": False, "transmission": 5, "biography": ""
    }
    cfg_MX = {
        "origin_country": "Mexico", "origin_city": "Mexico City", "dest_country": "USA", "dest_city": "Houston",
        "language": "Spanish", "age": 12, "anchor": 5, "language_use": 5, "homophily": 5, "density": "Medium",
        "institutional": False, "transmission": 5, "biography": ""
    }
    try:
        state_NG, _, _ = run_full_simulation(cfg_NG, {})
        state_MX, _, _ = run_full_simulation(cfg_MX, {})
        dims = ["language", "cultural_practice", "social_affiliation", "self_presentation"]
        deltas = {d: abs(state_NG["scores"][d] - state_MX["scores"][d]) for d in dims}
        sorted_deltas = sorted(deltas.values(), reverse=True)
        passed = sorted_deltas[0] >= 10 and sorted_deltas[1] >= 10
        outcome = "PASS" if passed else "FAIL"
        metrics = deltas
        trace_summary = f"Deltas: {deltas}"
        explanation = generate_llm_explanation("TC-06", outcome, metrics, expected_conditions["TC-06"], trace_summary)
        with open("TC-06_trace.json", "w") as f:
            json.dump({"Nigerian": state_NG, "Mexican": state_MX}, f, indent=2)
    except Exception as e:
        outcome = "FAIL"
        metrics = {"error": str(e)}
        explanation = f"Simulation error: {e}"
        passed = False
    csv_rows.append({
        "case_id": "TC-06",
        "case_type": "paired",
        "name": "Cross‑Cultural Validity",
        "outcome": outcome,
        "metric_value": ", ".join(f"{k}={v}" for k, v in metrics.items() if k != "error"),
        "expected": expected_conditions["TC-06"],
        "explanation": explanation
    })
    results["TC-06"] = {"passed": passed, "metrics": metrics}
    time.sleep(1)

    # TC-07: Personalisation Fidelity
    print("\nRunning TC-07 (Personalisation Fidelity)...")
    cfg_generic = {
        "origin_country": "Nigeria", "origin_city": "Lagos", "dest_country": "USA", "dest_city": "Houston",
        "language": "Yoruba", "age": 12, "anchor": 5, "language_use": 5, "homophily": 5, "density": "Medium",
        "institutional": False, "transmission": 5, "biography": ""
    }
    cfg_vivid = cfg_generic.copy()
    cfg_vivid["biography"] = "Every Sunday my grandmother made egusi soup while my father played Fela Kuti. I am terrified of losing my Yoruba accent and the smell of her kitchen."
    try:
        state_gen, _, _ = run_full_simulation(cfg_generic, {})
        state_viv, _, _ = run_full_simulation(cfg_vivid, {})
        mr_gen = compute_mr(state_gen["scores"])
        mr_viv = compute_mr(state_viv["scores"])
        delta = mr_viv - mr_gen
        passed = delta >= 8
        outcome = "PASS" if passed else "FAIL"
        metrics = {"mr_delta": delta}
        trace_summary = f"MR generic={mr_gen}, MR vivid={mr_viv}, delta={delta}"
        explanation = generate_llm_explanation("TC-07", outcome, metrics, expected_conditions["TC-07"], trace_summary)
        with open("TC-07_trace.json", "w") as f:
            json.dump({"generic": state_gen, "vivid": state_viv}, f, indent=2)
    except Exception as e:
        outcome = "FAIL"
        metrics = {"error": str(e)}
        explanation = f"Simulation error: {e}"
        passed = False
    csv_rows.append({
        "case_id": "TC-07",
        "case_type": "paired",
        "name": "Personalisation Fidelity",
        "outcome": outcome,
        "metric_value": f"MR delta = {metrics.get('mr_delta', 'N/A')}",
        "expected": expected_conditions["TC-07"],
        "explanation": explanation
    })
    results["TC-07"] = {"passed": passed, "metrics": metrics}
    time.sleep(1)

    # -----------------------------------------------------------------
    # SAVE CSV SUMMARY
    # -----------------------------------------------------------------
    csv_filename = "evaluation_results.csv"
    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "case_type", "name", "outcome", "metric_value", "expected", "explanation"])
        writer.writeheader()
        writer.writerows(csv_rows)

    # -----------------------------------------------------------------
    # PRINT SUMMARY
    # -----------------------------------------------------------------
    print("\n" + "="*80)
    print("EVALUATION SUMMARY – ALL 12 TEST CASES")
    print("="*80)
    for tc_id, res in results.items():
        status = "✅ PASS" if res.get("passed") else "❌ FAIL"
        print(f"{tc_id}: {status}")
        if "metrics" in res:
            print(f"   Metrics: {res['metrics']}")

    print(f"\nCSV saved to {csv_filename}")
    print("Detailed traces saved as JSON files (where applicable).")

if __name__ == "__main__":
    evaluate()