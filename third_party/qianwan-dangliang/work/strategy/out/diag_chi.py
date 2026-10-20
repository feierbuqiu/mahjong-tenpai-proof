import json, collections, itertools, math
R = json.load(open("work/strategy/out/fix_chi_v3_report.json", encoding="utf-8"))
print({k: R[k] for k in ("chiitoi_Wz_total","chiitoi_Wz_fixed","chiitoi_Wz_failed","chiitoi_residual_alpha6","codes_added")})
print("failed 例:", json.dumps(R["failed"][:4], ensure_ascii=False)[:600])
P = json.load(open("work/strategy/out/plan_k4_v2.json", encoding="utf-8"))
used = collections.Counter()
for r in P["plan"]:
    for c in r["codes"]: used[tuple(sorted(c))] += 1
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
HON = {"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def toz(s): return HON[s] if s in HON else "mps".index(s[-1])*9+int(s[0])-1
pairs_per_z = collections.Counter()
for mask, v in G["chiitoi_descriptors"].items():
    for d in v: pairs_per_z[toz(d["z"])] += 1
print("每个 z 的 (类,z) 计数 (前12):", pairs_per_z.most_common(12))
# 对出现最多的 z, 统计 528 个 (z,a,a,b) 多重集的饱和分布
for z, c in pairs_per_z.most_common(3):
    sat = 0; free = 0; partial = 0
    for a, b in itertools.combinations([t for t in range(34) if t != z], 2):
        mu = tuple(sorted((z,a,a,b))); u = used.get(mu,0)
        if u == 0: free += 1
        elif u >= 12: sat += 1
        else: partial += 1
    print("z=%d (被 %d 个 (类,z) 使用): 528 对里 空闲 %d, 部分占用 %d, 饱和 %d" % (z, c, free, partial, sat))
