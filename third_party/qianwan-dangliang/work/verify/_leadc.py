
import json,collections
P=json.load(open("work/recon/plan_k4_leadC.json",encoding="utf-8"))
print("keys:",list(P.keys()))
rows=P["plan"] if isinstance(P,dict) and "plan" in P else P
print("classes:",len(rows),"codes:",sum(len(r["codes"]) for r in rows))
print("empty:",sum(1 for r in rows if not r["codes"]))
print("meta:",{k:v for k,v in P.items() if k!="plan"} if isinstance(P,dict) else None)
print("sample:",rows[0])
cl=collections.Counter(len(r["codes"]) for r in rows)
print("code-count distribution (smallest):",sorted(cl.items())[:8])
