
import json, collections
p=json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan.json"))
print("type:", type(p))
if isinstance(p, dict):
    print("keys:", list(p.keys())[:20])
    for k,v in list(p.items())[:6]:
        print("  ",k,"=",str(v)[:200])
    if "classes" in p:
        cs=p["classes"]; print("n_classes in plan:", len(cs))
        c0=cs[0] if isinstance(cs,list) else list(cs.items())[0]
        print("sample:", str(c0)[:400])
else:
    print("len:", len(p)); print("sample:", str(p[0])[:400])
st=json.load(open(r"D:\DSH\MJ2\work\strategy\out\table_stats.json"))
print("table_stats:", json.dumps(st, ensure_ascii=False)[:400])
