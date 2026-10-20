
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
p=json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"))
HONOR={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def s2t(s):
    if s in HONOR: return HONOR[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def wkey(w): return frozenset(s2t(x) for x in w) if w and isinstance(w[0],str) else frozenset(w)
empty={wkey(x["W"]) for x in p["plan"] if not x.get("codes")}
def base_of(c): return c*9 if c<3 else 27
LETTER="mpsz"
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
small=collections.Counter(); tanki=collections.Counter()
for c in d["classes"]:
    if wkey(c["W"]) not in empty: continue
    for s in c["sources"]:
        if s.get("kind")=="I":
            A=parse_A(s["A"], LETTER.index(s["cat"]))
            if sum(A)<4: small["I"]+=1
        elif s.get("kind")=="II":
            A1=parse_A(s["minA1"], LETTER.index(s["cats"][0])); A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
            A=tuple(a+b for a,b in zip(A1,A2))
            if sum(A)<4: small["II"]+=1
print("classes:",len(empty), "blocks with |A|<4:", dict(small))
