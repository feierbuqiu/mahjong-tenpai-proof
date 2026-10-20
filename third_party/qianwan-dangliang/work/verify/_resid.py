
import json
d = json.load(open("work/verify/verify_report.json", encoding="utf-8"))
sc = d["source_checks"]
print("typeI_uncovered:", json.dumps(sc.get("typeI_uncovered"), ensure_ascii=False)[:500])
print("typeI_blocks:", sc.get("typeI_blocks"), "over_budget:", sc.get("typeI_over_budget"))
print("chiitoi samples:", sc.get("chiitoi_hand_samples"), "zero:", sc.get("chiitoi_zero_code"),
      "fails:", json.dumps(sc.get("chiitoi_fail_examples"), ensure_ascii=False)[:400])
sim = d["simulation"]
print("sim:", {k: sim[k] for k in ("samples","listening","classes_hit","coverage_fail","soundness_fail","bruteforce_checked","bruteforce_mismatch")})
print("sim coverage examples:", json.dumps(sim.get("coverage_examples"), ensure_ascii=False)[:400])
