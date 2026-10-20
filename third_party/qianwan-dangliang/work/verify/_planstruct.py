
import json
P=json.load(open("work/verify/plan_k4_final.json",encoding="utf-8"))
print("top keys:", list(P.keys()))
r=P["plan"][0]
print("entry keys:", list(r.keys()))
print("sample:", {k:(v if not isinstance(v,list) else v[:3]) for k,v in r.items()})
print("n classes:", len(P["plan"]), "total codes:", sum(len(x["codes"]) for x in P["plan"]))
print("meta-ish:", {k:v for k,v in P.items() if k!="plan"})
