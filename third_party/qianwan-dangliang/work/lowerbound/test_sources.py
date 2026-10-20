import sys, json, collections
sys.stdout.reconfigure(encoding="utf-8"); sys.path.insert(0,"work/lowerbound")
import k4_sources as KS
HONN=["E","S","W","N","Haku","Hatsu","Chun"]
def to_idx(w):
    o=[]
    for x in w:
        if isinstance(x,int): o.append(x)
        elif x in HONN: o.append(27+HONN.index(x))
        else: o.append("mps".index(x[-1])*9+int(x[0])-1)
    return o
G=json.load(open("work/data/out/global.json",encoding="utf-8"))
CH={}
for mask,v in G.get("chiitoi_descriptors",{}).items():
    W=frozenset(t for t in range(34) if (int(mask)>>t)&1); CH[W]=[to_idx([d["z"]])[0] for d in v]
print("表格 classes:", len(KS.cls_blocks()), " PROFI_D:", len(KS.table()["PROFI_D"]), " PROFII_D:", len(KS.table()["PROFII_D"]))
# verifier 的反例: 类 {1m} 的码 (1m,3p,3p,6p) 应判定可用
W=frozenset({0}); c=tuple(sorted(to_idx(["1m","3p","3p","6p"])))
print("反例检查 W={1m} code=", c, "->", KS.code_in_class(W,c,CH.get(W,[])))
# 之前误报的九莲类码 (E,E,E,1m)
W2=frozenset(range(9)); c2=tuple(sorted(to_idx(["E","E","E","1m"])))
print("九莲 W={1m..9m} code=(E,E,E,1m) ->", KS.code_in_class(W2,c2,CH.get(W2,[])))
