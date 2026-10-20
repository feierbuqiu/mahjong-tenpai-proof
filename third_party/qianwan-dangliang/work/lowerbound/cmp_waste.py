import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
A=json.load(open("work/lowerbound/waste_list.json",encoding="utf-8"))
print("lowerbound waste_list: total=%d classes=%d" % (A["total"], len(A["classes"])))
try:
    B=json.load(open("work/verify/waste_list_exact.json",encoding="utf-8"))
    print("verifier waste_list_exact keys:", list(B.keys()) if isinstance(B,dict) else type(B))
    print(json.dumps(B, ensure_ascii=False)[:600])
except Exception as e: print("verifier list err", e)
try:
    C=json.load(open("work/verify/waste_codes_report.json",encoding="utf-8"))
    print("verifier waste_codes_report keys:", list(C.keys()) if isinstance(C,dict) else type(C))
    print(json.dumps(C, ensure_ascii=False)[:800])
except Exception as e: print("report err", e)
