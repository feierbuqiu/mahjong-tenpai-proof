import sys, json, collections
sys.stdout.reconfigure(encoding="utf-8"); sys.path.insert(0,"work/lowerbound")
import k4_sources as KS
HONN=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HONN[t-27]
W=frozenset({9})   # 1p
print("类 {1p} 的块数:", len(KS.cls_blocks().get(W,[])))
for bi,blk in enumerate(KS.cls_blocks().get(W,[])):
    info=KS.block_index(W,bi,blk)
    if info[0]=="I": print("  block",bi,"I cat",info[1],"s",info[2],"x数",info[4])
    elif info[0]=="II": print("  block",bi,"II cats",info[1],info[2],"sizes",info[3],info[4],"x数",info[7],info[8])
    else: print("  block",bi,"KOK")
G=json.load(open("work/data/out/global.json",encoding="utf-8"))
CH={}
for mask,v in G.get("chiitoi_descriptors",{}).items():
    Wc=frozenset(t for t in range(34) if (int(mask)>>t)&1)
    CH[Wc]=[HONN.index(d["z"])+27 if d["z"] in HONN else "mps".index(d["z"][-1])*9+int(d["z"][0])-1 for d in v]
print("类 {1p} 是否在 chiitoi 描述子:", W in CH)
c=tuple(sorted([9,9,9,13]))  # 1p,1p,1p,5p
print("code:", [nm(t) for t in c], "->", KS.code_in_class(W,c,CH.get(W,[])))
# 手动检查: 存在 A 变体 (1p×4,5p×3)?
import itertools
cnt=0
for bi,blk in enumerate(KS.cls_blocks().get(W,[])):
    info=KS.block_index(W,bi,blk)
    if info[0]=="I" and info[1]==1 and info[2]==7:
        for X in KS.table()["PROFI_D"][(1,7,blk[1][2])][1]:
            xs=[X[i] for i in range(9)]
            if xs[0]>=3 and xs[4]>=1:
                cnt+=1
                if cnt<=3: print("   匹配 A 变体:", xs, " 求和", sum(xs))
print("含 {1p×3,5p×1} 的 |A|=7 变体数 =", cnt)
