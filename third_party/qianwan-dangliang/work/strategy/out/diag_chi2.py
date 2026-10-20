import json, collections, itertools
sys_path = None
P = json.load(open("work/strategy/out/plan_k4_v2.json", encoding="utf-8"))
used = collections.Counter()
for r in P["plan"]:
    for c in r["codes"]: used[tuple(sorted(c))] += 1
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
HON = {"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def toz(s): return HON[s] if s in HON else "mps".index(s[-1])*9+int(s[0])-1
def nm(t): 
    HN=["E","S","W","N","Haku","Hatsu","Chun"]
    return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HN[t-27]
def has_k6(P_pairs, verts, need=6):
    E = P_pairs
    def rec(cands, k):
        if k == 0: return True
        for i,v in enumerate(cands):
            if len(cands)-i < k: return False
            nxt=[u for u in cands[i+1:] if (min(v,u),max(v,u)) in E]
            if rec(nxt,k-1): return True
        return False
    return rec(verts, need)
wz = []
for mask, zs in sorted(G["chiitoi_descriptors"].items()):
    for d in zs: wz.append((int(mask), toz(d["z"])))
info = []
for mask, z in wz:
    verts=[t for t in range(34) if t != z]
    sat=set(); free=0; partial=0
    for a,b in itertools.combinations(verts,2):
        mu=tuple(sorted((z,a,a,b))); u=used.get(mu,0)
        if u>=12: sat.add((a,b))
        elif u==0: free+=1
        else: partial+=1
    k6 = has_k6(sat, verts)
    info.append((mask,z,len(sat),free,partial,k6))
bad = [x for x in info if x[5]]
print("(类,z) 总数 %d; 饱和图含 K6 的 = %d" % (len(info), len(bad)))
for x in bad[:10]:
    print("   类掩码 %d z=%s: 饱和 %d, 空闲 %d, 部分 %d  -> 饱和图有 K6 ⇒ 存在 6 张非 z 牌其任何对内都无空闲码 ⇒ 不换出容量就无法覆盖" % (x[0], nm(x[1]), x[2], x[3], x[4]))
print("饱和图无 K6 的 (W,z) 数 =", len(info)-len(bad))
j = [x for x in info if not x[5]]
for x in j[:5]: print("   可尝试: 类 %d z=%s 饱和 %d 空闲 %d 部分 %d" % (x[0], nm(x[1]), x[2], x[3], x[4]))
