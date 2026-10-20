
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
LETTER="mpsz"
def base_of(c): return c*9 if c<3 else 27
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
sizes=collections.Counter(); cls_with=set()
for c in d["classes"]:
    for s in c["sources"]:
        if s.get("kind")=="I":
            A=parse_A(s["A"], LETTER.index(s["cat"])); n=sum(A)
        elif s.get("kind")=="II":
            A1=parse_A(s["minA1"], LETTER.index(s["cats"][0])); A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
            n=sum(A1)+sum(A2)
        else: continue
        if 1<=n<=3:
            sizes[n]+=1; cls_with.add(c["Wmask"])
print("blocks with |A| in 1..3 :", dict(sizes), " classes affected:", len(cls_with), "of", len(d["classes"]))
