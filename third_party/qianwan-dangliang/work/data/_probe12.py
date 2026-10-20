# -*- coding: utf-8 -*-
"""_probe12.py -- cross-check global.json against the independent single-sector census."""
import json, sys, os
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
import mjcore as M

g = json.load(open(r"D:\DSH\MJ2\work\data\out\global.json", encoding="utf-8"))
s1 = json.load(open(r"D:\DSH\MJ2\work\data\out\single.json", encoding="utf-8"))
gcls = {c["Wmask"]: c for c in g["classes"]}
print("global classes:", len(gcls), " file bytes:", os.path.getsize(r"D:\DSH\MJ2\work\data\out\global.json"))
bad=0; notfound=0; lower=0
for key, cat in (("flush_m",0),("flush_p",1),("flush_s",2),("honors_z",3)):
    rows = s1[key]["tenpai_full_W"]["classes"]
    for r in rows:
        m = r["Wmask"]
        if m not in gcls:
            notfound += 1; continue
        gm = gcls[m]["mincount"]
        b = M.CAT_BASE[cat]; ln = M.CAT_LEN[cat]
        for i in range(ln):
            if gm[b+i] > r["mincount"][i]:
                bad += 1
                if bad <= 5: print("NOT <=:", key, r["W"], M.tile_name(b+i), gm[b+i], r["mincount"][i])
            if gm[b+i] < r["mincount"][i]:
                lower += 1
    print(key, "classes:", len(rows), "all present in global:", notfound==0)
print("mincount violations of global<=sector:", bad, " strictly lower tiles:", lower)
# sub-universe counts
for c, name in ((0,"m"),(1,"p"),(2,"s"),(3,"z")):
    b=M.CAT_BASE[c]; ln=M.CAT_LEN[c]; mask=((1<<ln)-1)<<b
    print("classes with W inside", name, ":", sum(1 for m in gcls if m & ~mask == 0))
# sample record
k = sorted(gcls)[1000]
print("sample class:", json.dumps(gcls[k], ensure_ascii=False)[:600])
print("meta:", json.dumps({kk:vv for kk,vv in g.items() if kk!="classes"}, ensure_ascii=False)[:900])
