
import json,hashlib,os
for p in ["work/recon/plan_k4_leadC.json","work/recon/plan_k4_leadD.json","work/verify/plan_k4_leadC_patched.json"]:
    if not os.path.exists(p): print(p,"(missing)"); continue
    b=open(p,"rb").read(); P=json.loads(b.decode("utf-8"))
    rows=P["plan"]
    print("%-46s sha256=%s  codes=%d classes=%d" % (p, hashlib.sha256(b).hexdigest()[:16], sum(len(r["codes"]) for r in rows), len(rows)))
