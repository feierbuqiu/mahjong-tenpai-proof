
import json
d = json.load(open("work/verify/verify_report.json", encoding="utf-8"))
sc = d["source_checks"]
print("typeI_uncovered:", json.dumps(sc.get("typeI_uncovered"), ensure_ascii=False)[:600])
print("typeI_blocks:", sc.get("typeI_blocks"), "over_budget:", sc.get("typeI_over_budget"))
print("chiitoi examples:", json.dumps(sc.get("chiitoi_fail_examples"), ensure_ascii=False)[:400])
f = json.load(open("work/verify/fastcov_report.json", encoding="utf-8"))
print("all_failures present:", {k: ("all_failures" in v, len(v["all_failures"])) for k, v in f["suits"].items()})
print("first m failure:", json.dumps(f["suits"]["m"]["all_failures"][0], ensure_ascii=False))
