
import json
p=json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"))
plan=p["plan"]
# map tile indices to names using global.json W masks
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
LETTER="mpsz"
def t2s(t): return ("%d%s"%((t%9)+1,LETTER[t//9])) if t<27 else ("%dz"%((t-27)+1))
empty=[x for x in plan if not x.get("codes")]
print("empty classes:", len(empty))
for x in empty[:12]:
    W=x.get("W")
    if W and isinstance(W[0],int): W=[t2s(t) for t in W]
    print("   W=",W,"codes=",x.get("codes"),"modes=",str(x.get("modes"))[:120])
