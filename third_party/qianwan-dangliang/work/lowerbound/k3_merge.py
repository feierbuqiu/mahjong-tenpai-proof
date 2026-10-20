# -*- coding: utf-8 -*-
import json, glob, os
allr=[]
for p in glob.glob("work/lowerbound/k3_u_*.json")+["work/lowerbound/k3_subuniverse.json"]:
    if not os.path.exists(p): continue
    try:
        d=json.load(open(p,encoding="utf-8"))
        for r in d.get("results",[]):
            r["src"]=os.path.basename(p); allr.append(r)
    except Exception as e:
        print("ERR",p,e)
# 去重按 U
seen={}
for r in allr:
    seen[tuple(r["U"])]=r
allr=sorted(seen.values(), key=lambda r:-r["ratio"])
print("共测 U 个数 =", len(allr), " 否证个数 =", sum(1 for r in allr if r["disproved"]))
print()
print("%-24s %3s %8s %6s %6s %7s %7s" % ("tag","|U|","budget","N","L","N+L","ratio"))
for r in allr[:15]:
    print("%-24s %3d %8d %6d %6d %7d %7.3f %s" % (r["tag"], r["|U|"], r["budget"], r["N"], r["L"], r["N_plus_L"], r["ratio"], "*** 否证 ***" if r["disproved"] else ""))
print()
from collections import defaultdict
by=defaultdict(list)
for r in allr: by[r["|U|"]].append(r["ratio"])
print("按 |U| 的最佳比值:")
for n in sorted(by): print("  |U|=%2d: 最好 ratio=%.3f  (U 个数 %d)" % (n, max(by[n]), len(by[n])))
json.dump({"n_U":len(allr),"n_disproved":sum(1 for r in allr if r["disproved"]),"top":allr[:20]}, open("work/lowerbound/k3_summary.json","w"), ensure_ascii=False, indent=1)
