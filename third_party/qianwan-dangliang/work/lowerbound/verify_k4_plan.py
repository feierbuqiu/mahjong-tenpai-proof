# -*- coding: utf-8 -*-
"""verify_k4_plan.py --- lowerbound 侧独立终验 (不 import verifier 的任何模块)
用法: python -u work/lowerbound/verify_k4_plan.py <plan.json> [--sim N] [--json out] [--typeI-limit N]
"""
import sys, os, json, itertools, collections, random, time, math
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lower import waits, melds_only
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def nm(t): return ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONN[t-27]
def to_idx(w):
    o = []
    for x in w:
        if isinstance(x, int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9 + int(x[0]) - 1)
    return o
SU = {"m":0,"p":1,"s":2,"z":3}
def contains(h, c):
    need = {}
    for t in c: need[t] = need.get(t,0)+1
    return all(h[t] >= v for t,v in need.items())
def parse(ds, ci):
    off = (0,9,18,27)[ci]; u = [0]*34
    for i,ch in enumerate(ds):
        if ch != "0": u[off+i] = int(ch)
    return tuple(u)
def p4(mu):
    cc = collections.Counter(mu); return 24 // math.prod(math.factorial(v) for v in cc.values())

PLANP = "work/verify/plan_k4_final.json"
SIM = 1000000; OUTJSON = os.path.join(HERE, "verify_k4_report.json"); T1LIM = 0
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--sim": SIM = int(args[i+1]); i += 2
    elif args[i] == "--json": OUTJSON = args[i+1]; i += 2
    elif args[i] == "--typeI-limit": T1LIM = int(args[i+1]); i += 2
    else: PLANP = args[i]; i += 1

P = json.load(open(PLANP, encoding="utf-8"))
K = P.get("k", 4); rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
cls = {}; order = []
for r in rows:
    W = frozenset(to_idx(r["W"])); cls[W] = [tuple(c) for c in r["codes"]]; order.append(W)
allcodes = [c for W in order for c in cls[W]]
log("plan = %s : k=%d, 类 %d, 码 %d" % (PLANP, K, len(cls), len(allcodes)))
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
GCLS = {frozenset(to_idx(r["W"])) for r in G["classes"]}
rep = {"plan": PLANP, "k": K, "n_classes": len(cls), "n_codes": len(allcodes)}

sym = set(cls) ^ GCLS
rep["check1_class_set_equal"] = (len(sym) == 0); rep["check1_symdiff"] = len(sym)
log("① 类集对称差 = %d %s" % (len(sym), "OK" if not sym else "FAIL"))
empty = [sorted(W) for W in cls if not cls[W]]
rep["check2_empty_classes"] = len(empty); log("② 空类 = %d" % len(empty))
dup = len(allcodes) - len(set(allcodes)); rep["check3_code_collisions"] = dup
cntm = collections.Counter(tuple(sorted(c)) for c in allcodes)
over = [(mu,n) for mu,n in cntm.items() if n > p4(mu)]
rep["check3_multiset_over_capacity"] = len(over); rep["check3_max_use"] = max(cntm.values()) if cntm else 0
log("③ 有序码冲突 = %d ; 超容量多重集 = %d (最大用量 %d)" % (dup, len(over), rep["check3_max_use"]))

# ---------------- 元素表 ----------------
ELEMS = collections.defaultdict(list); EIDX = collections.defaultdict(lambda: collections.defaultdict(list))
def add_elem(W, v):
    ELEMS[W].append(v)
    for t in set(i for i in range(34) if v[i] > 0):
        EIDX[W][t].append(len(ELEMS[W])-1)
KOK = tuple(sorted([0,8,9,17,18,26]+list(range(27,34))))
kok_hands = []
H13 = [0]*34
for t in KOK: H13[t] = 1
kok_hands.append(tuple(H13))
for miss in KOK:
    for dup_ in KOK:
        if dup_ == miss: continue
        h = list(H13); h[miss] = 0; h[dup_] += 1
        kok_hands.append(tuple(h))
for row in G["classes"]:
    W = frozenset(to_idx(row["W"]))
    for s in row.get("sources", []):
        if s["kind"] == "I": add_elem(W, parse(s["A"], SU[s["cat"]]))
        elif s["kind"] == "II":
            cats = s["cats"]; u = [0]*34
            for k_,ch in enumerate(s["minA1"]):
                if ch != "0": u[(0,9,18,27)[SU[cats[0]]]+k_] = int(ch)
            for k_,ch in enumerate(s["minA2"]):
                if ch != "0": u[(0,9,18,27)[SU[cats[1]]]+k_] += int(ch)
            add_elem(W, tuple(min(4,x) for x in u))
        elif s["kind"] == "kokushi":
            for h in kok_hands: add_elem(W, h)
CHIIT = {}
for mask, v in G.get("chiitoi_descriptors", {}).items():
    W = frozenset(t for t in range(34) if (int(mask)>>t)&1)
    CHIIT[W] = [to_idx([d["z"]])[0] for d in v]
log("元素表: %d 元素 / %d 类; chiitoi 描述子 %d 类" % (sum(len(v) for v in ELEMS.values()), len(ELEMS), len(CHIIT)))

# ---------------- 全量手牌 (单花色 3 门 + 纯字牌) ----------------
FULLHANDS = {}
def suit_hands(base, ntypes):
    out = collections.defaultdict(list)
    for c in itertools.product(range(5), repeat=ntypes):
        if sum(c) != 13: continue
        cnt = [0]*34
        for j,v in enumerate(c):
            if v: cnt[base+j] = v
        W = waits(tuple(cnt))
        if W: out[frozenset(W)].append(tuple(cnt))
    return out
for base, nt, tag in ((0,9,"m"),(9,9,"p"),(18,9,"s"),(27,7,"z")):
    d = suit_hands(base, nt)
    for W, hs in d.items(): FULLHANDS.setdefault(W, []).extend(hs)
    log("   全量手牌 %s: %d 类 %d 手" % (tag, len(d), sum(len(v) for v in d.values())))
FHIDX = collections.defaultdict(lambda: collections.defaultdict(list))
for W, hs in FULLHANDS.items():
    for idx, h in enumerate(hs):
        for t in set(i for i in range(34) if h[i] > 0): FHIDX[W][t].append(idx)

# ---------------- ④ 每码 ⊆ 该类某手牌 (精确: A 变体表) ----------------
import k4_sources as KS
def elem_hit(W, c):
    el = ELEMS.get(W)
    if not el: return False
    idx = EIDX[W]
    rarest = min(set(c), key=lambda t: len(idx.get(t, ())))
    for i in idx.get(rarest, ()):
        if contains(el[i], c): return True
    return False
def hand_hit(W, c):
    hs = FULLHANDS.get(W)
    if not hs: return False
    idx = FHIDX[W]
    rarest = min(set(c), key=lambda t: len(idx.get(t, ())))
    for i in idx.get(rarest, ()):
        if contains(hs[i], c): return True
    return False
MELD_CACHE = {}
def meld_vecs(cat, s):
    key = (cat, s)
    if key in MELD_CACHE: return MELD_CACHE[key]
    Ln = (9,9,9,7)[cat]; off = (0,9,18,27)[cat]; out = []
    if s == 0: out = [tuple([0]*34)]
    else:
        for combo in itertools.combinations_with_replacement(range(Ln), s):
            v = [0]*Ln
            for x in combo: v[x] += 1
            if max(v) > 4: continue
            if cat == 3:
                if all(x % 3 == 0 for x in v): out.append(tuple([0]*off+v+[0]*(34-off-Ln)))
            elif melds_only(tuple(v)) is not None:
                out.append(tuple([0]*off+v+[0]*(34-off-Ln)))
    MELD_CACHE[key] = out; return out
CAT_OF = [0]*9+[1]*9+[2]*9+[3]*7
def tanki_code_ok(c, x):
    """单元素类 {x}: 手牌 = x + (x 所在类别之外) 4 个面子。
    码 c ⊆ 某手牌 <=> c 中 x 至多 1 个, 其余牌都不在 cat(x), 且可用 <=4 个刻子/顺子容纳。"""
    cc = collections.Counter(c)
    if cc.get(x, 0) > 1: return False
    groups = 0
    for t, k in cc.items():
        if t == x: continue
        if CAT_OF[t] == CAT_OF[x]: return False
        if k > 4: return False
        groups += 2 if k == 4 else 1
    return groups <= 4
def build_hand_from_code(W, c, tries=300):
    """为单元素类 {x}(tanki/纯七对子)构造 H ⊇ c 且 waits(H)==W"""
    if len(W) != 1: return None
    x = next(iter(W)); cc = collections.Counter(c)
    rng = random.Random(hash(c) & 0xffff)
    for _ in range(tries):
        H = [0]*34; H[x] = 1
        rem = dict(cc)
        if rem.get(x, 0) > 0: rem[x] -= 1
        ok = True; nmelds = 1
        for t, k in list(rem.items()):
            while k > 0:
                need = min(k, 3)
                if k == 4:
                    # 4 张同牌: 一刻子 + 一张(需另找含 t 的面子) —— 用相邻顺子凑
                    if t < 27 and t % 9 <= 6 and H[t+1] < 4 and H[t+2] < 4:
                        H[t] += 1; H[t+1] += 1; H[t+2] += 1; k -= 1; nmelds += 1
                        if k > 0: H[t] += 3; k -= 3; nmelds += 1
                    else: ok = False; break
                else:
                    H[t] += 3; k -= need; nmelds += 1
            if not ok: break
        if not ok: continue
        # 补足到 13 张: 只用"手牌中还没有的牌"的刻子 (绝不能加 x, 会破坏 tanki 结构)
        pool = [t for t in range(34) if H[t] == 0 and t != x]
        rng.shuffle(pool)
        for t in pool:
            if sum(H) >= 13: break
            H[t] = 3
        if sum(H) != 13 or max(H) > 4: continue
        Ht = tuple(H)
        if waits(Ht) == W and contains(Ht, c): return Ht
    return None
# ---- 来源级嵌入: 码 c ⊆ 某来源块的手牌 (构造性, 不使用 waits) ----
SRC = collections.defaultdict(list)
for row in G["classes"]:
    W0 = frozenset(to_idx(row["W"]))
    for s in row.get("sources", []):
        if s["kind"] == "I":
            ci = SU[s["cat"]]; A = parse(s["A"], ci); j = (13 - sum(A)) // 3
            SRC[W0].append(("I", ci, A, [SU[x] for x in s["inert"]], j, None, None, None))
        elif s["kind"] == "II":
            c1, c2 = SU[s["cats"][0]], SU[s["cats"][1]]
            u1 = parse(s["minA1"], c1); u2 = parse(s["minA2"], c2)
            j = (13 - sum(u1) - sum(u2)) // 3
            SRC[W0].append(("II", None, None, [SU[x] for x in s["inert"]], max(j,0), u1, c1, u2, c2))
def ok_meld_group(g):
    if len(g) <= 2: return True
    if len(g) == 3:
        if len(set(g)) == 1: return True
        sd = sorted(g)
        return len(set(sd)) == 3 and CAT_OF[sd[0]] == CAT_OF[sd[2]] < 3 and sd[1] == sd[0]+1 and sd[2] == sd[1]+1
    return False
def min_parts(R):
    if not R: return 0
    best = [99]
    def rec(rem, parts):
        if parts >= best[0]: return
        if not rem:
            best[0] = parts; return
        first = rem[0]; rest = rem[1:]
        for size in (1,2,3):
            for combo in itertools.combinations(range(len(rest)), size-1):
                grp = [first] + [rest[i] for i in combo]
                if ok_meld_group(grp):
                    rem2 = [rest[i] for i in range(len(rest)) if i not in combo]
                    rec(rem2, parts+1)
    rec(sorted(R), 0)
    return best[0]
def src_embed(W, c):
    cc = collections.Counter(c)
    for src in SRC.get(W, []):
        kind, ci, A, inert_ci, j = src[0], src[1], src[2], src[3], src[4]
        if kind == "I":
            if any(CAT_OF[t] == ci and A[t] < k for t, k in cc.items()): continue
            R = [t for t, k in cc.items() if CAT_OF[t] != ci for _ in range(k)]
            if any(CAT_OF[t] not in inert_ci for t in R): continue
            if min_parts(R) <= j: return True
        else:
            u1, c1, u2, c2 = src[5], src[6], src[7], src[8]
            if any((CAT_OF[t] == c1 and u1[t] < k) or (CAT_OF[t] == c2 and u2[t] < k) for t, k in cc.items()): continue
            R = [t for t, k in cc.items() if CAT_OF[t] not in (c1, c2) for _ in range(k)]
            if any(CAT_OF[t] not in inert_ci for t in R): continue
            if min_parts(R) <= j: return True
    return False
code_bad = []; via_full = 0; via_elem = 0; via_chi = 0; via_tanki = 0; via_src = 0; tanki_samples = []
for W in order:
    codes = cls[W]; zs = CHIIT.get(W); single = (len(W) == 1)
    for c in codes:
        _ok, _why = KS.code_in_class(W, c, zs if zs else [])
        if _ok: via_src += 1; continue
        if hand_hit(W, c): via_full += 1; continue
        if elem_hit(W, c): via_elem += 1; continue
        if zs:
            cc = collections.Counter(c)
            zt = [t for t in cc if (t in zs) and cc[t] == 1]
            done = False
            if zt:
                z0 = zt[0]; others = {t:n for t,n in cc.items() if t != z0}
                if all(n <= 2 for n in others.values()) and len(others) <= 6:
                    S = sorted(others); pool = [t for t in range(34) if t != z0 and t not in others]
                    Kk = S + pool[:6-len(S)]
                    H = [0]*34; H[z0] = 1
                    for t in Kk: H[t] = 2
                    if sum(H) == 13 and waits(tuple(H)) == W and contains(tuple(H), c): done = True
            if done: via_chi += 1; continue
        if src_embed(W, c): via_src += 1; continue
        if single and tanki_code_ok(c, next(iter(W))):
            via_tanki += 1
            if len(tanki_samples) < 300:
                H = build_hand_from_code(W, c)
                tanki_samples.append(([nm(t) for t in sorted(W)], [nm(t) for t in c], H is not None))
            continue
        code_bad.append({"W": [nm(t) for t in sorted(W)], "code": [nm(t) for t in c]})
rep["check4_total"] = len(allcodes); rep["check4_unverified"] = len(code_bad)
rep["check4_via"] = {"full_hand": via_full, "element": via_elem, "source_embedding": via_src,
                      "chiitoi_construction": via_chi, "tanki_criterion": via_tanki}
rep["check4_tanki_sample_witness_fail"] = sum(1 for s in tanki_samples if not s[2]) 
rep["check4_tanki_sample_examples"] = [s for s in tanki_samples if not s[2]][:5]
log("④ 码 ⊆ 手牌: 通过 %d/%d (全量手牌 %d, 元素 %d, 来源嵌入 %d, 七对构造 %d, tanki 判据 %d, 未证实 %d)" % (
    len(allcodes)-len(code_bad), len(allcodes), via_full, via_elem, via_src, via_chi, via_tanki, len(code_bad)))
if code_bad: log("   未证实例: %s" % code_bad[:5])

# ---------------- ⑤ 逐类命中集: 全部来源块 × 全部 A 变体 × 补牌族 ----------------
FILLC = {}
def fillers(inert_ci, m, mode=None):
    key = (tuple(inert_ci), m, mode)
    if key in FILLC: return FILLC[key]
    out = []
    def ischi(F):
        return all(x in (0,2) for x in F)
    def rec(i, rem, acc):
        if i == len(inert_ci):
            if rem == 0:
                if mode == "chi" and not ischi(acc): return
                if mode == "nochi" and ischi(acc): return
                out.append(tuple(acc))
            return
        for s in range(0, rem+1, 3):
            for v in meld_vecs(inert_ci[i], s):
                nxt = [acc[j]+v[j] for j in range(34)]
                rec(i+1, rem-s, nxt)
    rec(0, m, [0]*34)
    FILLC[key] = out; return out
def local_to34(vec_local, ci):
    v = [0]*34; off = (0,9,18,27)[ci]
    for i,x in enumerate(vec_local):
        if x: v[off+i] = x
    return tuple(v)
TBL = KS.table()
BLOCKS = TBL["cls"]
t1_tot = 0; t1_unc = 0; t1_bad = []
cov_log = []
_ncls = 0
for W in order:
    _ncls += 1
    if _ncls % 200 == 0:
        log("    ⑤ 进度 %d/%d 类, 单元 %d, 未覆盖 %d" % (_ncls, len(order), t1_tot, t1_unc))
    codes = cls[W]
    ms = [tuple(sorted(c)) for c in codes]
    specs = []
    for mu in ms:
        sp = {}
        for t in mu: sp[t] = sp.get(t, 0) + 1
        specs.append(sorted(sp.items()))
    def hitA(Xv):
        for sp in specs:
            ok = True
            for t, need in sp:
                if Xv[t] < need: ok = False; break
            if ok: return True
        return False
    def hitAB(Av, Bv):
        for sp in specs:
            ok = True
            for t, need in sp:
                if Av[t] + Bv[t] < need: ok = False; break
            if ok: return True
        return False
    for bi, blk in enumerate(BLOCKS.get(W, [])):
        kind = blk[0]; mode = blk[3] if len(blk) > 3 else None
        if kind == "KOK":
            t1_tot += 1
            hand = tuple(blk[1])
            if not any(contains(hand, mu) for mu in ms):
                t1_unc += 1
                if len(t1_bad) < 10: t1_bad.append({"W": [nm(t) for t in sorted(W)], "block": "KOK",
                                                    "hand": [nm(t) for t in range(34) for _ in range(hand[t])]})
            continue
        if kind == "I":
            (c_i, s, pkey) = blk[1]
            am, xs = TBL["PROFI_D"][(c_i, s, pkey)]
            inert = [c for c in range(4) if c != c_i]; j = (13 - s) // 3
            FL = fillers(inert, 3*j, "chi" if mode == "chi" else ("nochi" if mode == "nochi" else None))
            for X in xs:
                t1_tot += 1
                Xv = local_to34(X, c_i)
                if hitA(Xv): continue
                bad = None
                for F in FL:
                    if not hitAB(Xv, F):
                        bad = tuple(Xv[q] + F[q] for q in range(34)); break
                if bad is not None:
                    t1_unc += 1
                    if len(t1_bad) < 10:
                        t1_bad.append({"W": [nm(t) for t in sorted(W)], "block": "I", "mode": mode,
                                       "cat": c_i, "|A|": s, "nA_variants": len(xs),
                                       "A": [nm(t) for t in range(34) for _ in range(Xv[t])],
                                       "witness_hand": [nm(t) for t in range(34) for _ in range(bad[t])]})
        else:
            (c1, s1, k1) = blk[1]; (c2, s2, k2) = blk[2]
            am1, xs1 = TBL["PROFII_D"][(c1, s1, k1)]; am2, xs2 = TBL["PROFII_D"][(c2, s2, k2)]
            inert = [c for c in range(4) if c not in (c1, c2)]; j = (13 - s1 - s2)//3
            FL = fillers(inert, 3*j, "chi" if mode == "chi" else ("nochi" if mode == "nochi" else None))
            for X1 in xs1:
                v1 = local_to34(X1, c1)
                for X2 in xs2:
                    t1_tot += 1
                    v2 = local_to34(X2, c2)
                    b0 = tuple(v1[q] + v2[q] for q in range(34))
                    if hitA(b0): continue
                    bad = None
                    for F in FL:
                        if not hitAB(b0, F):
                            bad = tuple(b0[q] + F[q] for q in range(34)); break
                    if bad is not None:
                        t1_unc += 1
                        if len(t1_bad) < 10:
                            t1_bad.append({"W": [nm(t) for t in sorted(W)], "block": "II", "mode": mode,
                                           "sizes": [s1, s2], "nA_variants": [len(xs1), len(xs2)],
                                           "A": [nm(t) for t in range(34) for _ in range(b0[t])],
                                           "witness_hand": [nm(t) for t in range(34) for _ in range(bad[t])]})
rep["check5_units_scanned"] = t1_tot; rep["check5_units_uncovered"] = t1_unc
rep["check5_uncovered_examples"] = t1_bad
log("⑤ 逐类命中集(全 A 变体 × 补牌族): 单元 %d, 未覆盖 %d" % (t1_tot, t1_unc))
if t1_bad: log("   例: %s" % (t1_bad[:2],))

# ---------------- ⑥ chiitoi 精确 ----------------
def bad_K(W, z):
    pairs = set(); triples = set()
    for c in cls[W]:
        cc = collections.Counter(c)
        if any(v > (1 if t == z else 2) for t,v in cc.items()): continue
        S = tuple(sorted(t for t in cc if t != z))
        if len(S) == 2: pairs.add(S)
        elif len(S) == 3: triples.add(S)
    adj = [[False]*34 for _ in range(34)]
    for a,b in pairs: adj[a][b] = adj[b][a] = True
    tri = triples
    def rec(cands, chosen):
        if len(chosen) == 6:
            return list(chosen) if all(tuple(sorted(s)) not in tri for s in itertools.combinations(chosen,3)) else None
        for i,v in enumerate(cands):
            if len(cands)-i < 6-len(chosen): return None
            if any(adj[v][u] for u in chosen): continue
            nxt = [u for u in cands[i+1:] if not adj[v][u]]
            r = rec(nxt, chosen+[v])
            if r is not None: return r
        return None
    return rec([t for t in range(34) if t != z], [])
chi_bad = []
for W, zs in CHIIT.items():
    if W not in cls: chi_bad.append({"W": [nm(t) for t in sorted(W)], "z": None}); continue
    for z in zs:
        K = bad_K(W, z)
        if K: chi_bad.append({"W": [nm(t) for t in sorted(W)], "z": nm(z), "bad_K": [nm(t) for t in K]})
rep["check6_chiitoi_descriptors"] = sum(len(v) for v in CHIIT.values()); rep["check6_chiitoi_fail"] = len(chi_bad)
rep["check6_chiitoi_fail_examples"] = chi_bad[:6]
log("⑥ chiitoi: 描述子 %d, 失败 %d (例: %s)" % (rep["check6_chiitoi_descriptors"], len(chi_bad), chi_bad[:2]))

# ---------------- ⑦ 国士 ----------------
kok_bad = []
for row in G["classes"]:
    W = frozenset(to_idx(row["W"]))
    if W not in cls: continue
    if not any(s["kind"] == "kokushi" for s in row.get("sources", [])): continue
    for h in kok_hands:
        if waits(h) != W: continue
        if not any(contains(h, c) for c in cls[W]): kok_bad.append({"W": [nm(t) for t in sorted(W)]})
rep["check7_kokushi_fail"] = len(kok_bad); log("⑦ 国士: 失败 %d" % len(kok_bad))

# ---------------- ⑧ 模拟 ----------------
rng = random.Random(20240614)
CATS = ((9,0),(9,9),(9,18),(7,27))
def rv(ci, n):
    Ln, off = CATS[ci]; c = [0]*Ln
    for _ in range(n):
        while True:
            x = rng.randrange(Ln)
            if c[x] < 4: c[x] += 1; break
    return c
stats = collections.Counter(); fails = []; nocls_ex = []
for it in range(SIM):
    t = rng.random(); H = [0]*34
    if t < 0.25:
        ci = rng.randrange(4); n = rng.choice([1,4,7,10,13]); X = rv(ci, n)
        for j,x in enumerate(X): H[CATS[ci][1]+j] += x
        rem = 13-n
        for idx,cj in enumerate([c for c in range(4) if c != ci]):
            left = 3-idx-1
            cand = [s for s in range(0, rem+1, 3) if rem-s <= 12*left and meld_vecs(cj, s)]
            if not cand: break
            s = rng.choice(cand)
            if s:
                v = rng.choice(meld_vecs(cj, s))
                H = [H[j]+v[j] for j in range(34)]
            rem -= s
    elif t < 0.7:
        c1, c2 = rng.sample(range(4), 2); n1 = rng.choice([2,5,8,11]); n2 = rng.choice([2,5,8,11])
        if n1+n2 > 13: n1, n2 = 2, 2
        for cc, nn in ((c1,n1),(c2,n2)):
            X = rv(cc, nn)
            for j,x in enumerate(X): H[CATS[cc][1]+j] += x
        rem = 13-n1-n2
        for idx,cj in enumerate([c for c in range(4) if c not in (c1,c2)]):
            left = 2-idx-1
            cand = [s for s in range(0, rem+1, 3) if rem-s <= 12*left and meld_vecs(cj, s)]
            if not cand: break
            s = rng.choice(cand)
            if s:
                v = rng.choice(meld_vecs(cj, s))
                H = [H[j]+v[j] for j in range(34)]
            rem -= s
    elif t < 0.9:
        ts = rng.sample(range(34), 7); z = ts[0]
        for x in ts[1:]: H[x] = 2
        H[z] = 1
    elif t < 0.95:
        ks = rng.sample(KOK, 12)
        for x in ks: H[x] = 1
        H[rng.choice(ks)] += 1
    else:
        for _ in range(13):
            while True:
                x = rng.randrange(34)
                if H[x] < 4: H[x] += 1; break
    H = tuple(H)
    if max(H) > 4: continue
    Wt = waits(H)
    if not Wt: continue
    W = frozenset(Wt)
    stats["listening"] += 1
    cs = cls.get(W)
    if not cs:
        stats["no_class"] += 1
        if len(nocls_ex) < 5: nocls_ex.append({"W": [nm(t) for t in sorted(W)], "hand": [nm(t) for t in range(34) for _ in range(H[t])]})
        continue
    if not any(contains(H, c) for c in cs):
        stats["fail"] += 1
        if len(fails) < 5: fails.append({"W": [nm(t) for t in sorted(W)], "hand": [nm(t) for t in range(34) for _ in range(H[t])]})
rep["check8_sim_target"] = SIM; rep["check8_sim_result"] = dict(stats); rep["check8_fail_examples"] = fails; rep["check8_no_class_examples"] = nocls_ex
log("⑧ 模拟 %d 手: 听牌 %d, 无类 %d, 覆盖失败 %d" % (SIM, stats["listening"], stats["no_class"], stats["fail"]))

rep["VERDICT_k4_plan_ok"] = (len(sym)==0 and not empty and dup==0 and not over and not code_bad
                             and t1_unc==0 and not T1LIM and not chi_bad and not kok_bad
                             and stats["fail"]==0 and stats["no_class"]==0)
log("=== 结论: %s ===" % ("k=4 plan 通过全部检查 ✓" if rep["VERDICT_k4_plan_ok"] else "未通过 (见报告)"))
json.dump(rep, open(OUTJSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("写出 %s" % OUTJSON)
