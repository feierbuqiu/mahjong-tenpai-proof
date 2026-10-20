
import json,hashlib
a=json.load(open("work/lowerbound/verify_k4_FINAL.json",encoding="utf-8"))
print("keys:",list(a.keys()))
for k,v in a.items():
    if k in ("check5_typeI_uncovered_examples","check6_chiitoi_fail_examples","check7_kokushi_examples"): continue
    s=json.dumps(v,ensure_ascii=False)
    print("  %-38s %s" % (k, s[:150]))
sha=hashlib.sha256(open("work/verify/plan_k4_FINAL.json","rb").read()).hexdigest()
print("plan sha256:",sha)
cert=json.load(open("work/verify/final_certificate.json",encoding="utf-8"))
print("cert plan path:",cert["plan"]["path"])
print("cert sha256   :",cert["plan"]["sha256"])
print("cert == file sha:", cert["plan"]["sha256"]==sha)
print("cert n_codes:",cert["plan"]["n_codes"], " file n_codes:", json.load(open("work/verify/plan_k4_FINAL.json",encoding="utf-8"))["n_codes"])
