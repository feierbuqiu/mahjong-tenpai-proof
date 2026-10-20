# -*- coding: utf-8 -*-
"""check.py -- T4 自检: 结构化全称判据 + 码不交/decode 一致 + 子宇宙预算 + 手牌级模拟。
输出 out/check.json
"""
import sys, os, json, time, random, itertools, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
import strategy as SG
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)

PLANP = os.environ.get("PLAN", os.path.join(OUT, "plan.json"))
plan = json.load(open(PLANP, encoding="utf-8"))
K = plan["k"]
SG.K = K
_CACHE = os.path.join(OUT, "table_cache.pkl")
if os.path.exists(_CACHE):
    import pickle as _pk
    T = _pk.load(open(_CACHE, "rb")); log("table: cached")
else:
    T = TL.build(); log("table: built")
CLS = T["cls"]
PROFI_D = T["PROFI_D"]; PROFII_D = T["PROFII_D"]
log("plan: k=%d classes=%d codes=%d budget=%d fails=%d" % (K, plan["n_classes"], plan["n_codes"], 34**K, len(plan.get("fails", []))))
rep = {"plan_file": PLANP, "k": K, "n_classes": plan["n_classes"], "n_codes": plan["n_codes"], "budget": 34**K,
       "plan_fails": plan.get("fails", [])}

def contains(vec, m):
    need = {}
    for x in m: need[x] = need.get(x, 0)+1
    return all(vec[x] >= v for x, v in need.items())
_HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def _Widx(w):
    """W 兼容: 34 位掩码(int) / 牌索引 list / 牌名 list"""
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    out = []
    for x in w:
        if isinstance(x, int): out.append(x)
        elif x in _HON: out.append(_HON[x])
        else: out.append("mps".index(x[-1])*9 + int(x[0]) - 1)
    return out

class_to_codes = {}; modes_of = {}
seen = {}; dup = 0
for pc in plan["plan"]:
    W = frozenset(_Widx(pc["W"])); cs = [tuple(c) for c in pc["codes"]]
    class_to_codes[W] = cs; modes_of[W] = pc.get("modes", [])
    for c in cs:
        if c in seen and seen[c] != W: dup += 1
        seen[c] = W
rep["distinct_codes"] = len(seen); rep["code_collisions"] = dup
rep["sum_S_C"] = sum(len(v) for v in class_to_codes.values())
rep["classes_planned"] = len(class_to_codes)
rep["classes_missing"] = len(CLS) - len(class_to_codes)
log("有序码 %d, 冲突 %d, Σ|S_C| = %d, 缺类 %d" % (len(seen), dup, rep["sum_S_C"], rep["classes_missing"]))

# ---------- 1) 结构化全称判据(元素级去重) ----------
fail = []; tot_elems = 0
tanki_cache = {}
def tanki_ok(x, S, reserved):
    reserved = [tuple(m) for m in reserved]
    key = (x, S, tuple(sorted(reserved)))
    if key in tanki_cache: return tanki_cache[key]
    fam = TL.fam_list(S, 12, True) + TL.fam_list(S, 12, False)
    pats = [tuple(c) for c in reserved]
    ok = True
    for F in fam:
        hit = False
        for c in pats:
            need = {}
            for t in c: need[t] = need.get(t, 0)+1
            if all(need.get(t, 0) <= (1 if t == x else F[t]) for t in need): hit = True; break
        if not hit: ok = False; break
    tanki_cache[key] = ok
    return ok

for pc in plan["plan"]:
    W = frozenset(_Widx(pc["W"])); codes = class_to_codes.get(W)
    if codes is None:
        fail.append([sorted(W), "not-in-CLS"]); continue
    blocks = CLS.get(W, []); modes = pc.get("modes", [])
    keys, cands, m2 = SG.class_elements(T, W, blocks)
    if len(modes) != len(blocks): modes = m2
    tot_elems += len(keys)
    for key in keys:
        v = key[2] if key[0] == "S" else key[1]
        if not any(contains(v, cc) for cc in codes):
            fail.append([sorted(W), "elem", key[0]]); break
    # tanki 块: 由保留码族覆盖补牌族
    for b, md in zip(blocks, modes):
        if md[0] != "tanki": continue
        (c, s, pkey) = b[1]; am, xs = PROFI_D[(c, s, pkey)]
        x = CAT_BASE[c] + next(i for i, v in enumerate(xs[0]) if v > 0)
        S = tuple(t for t in range(4) if t != c)
        if not tanki_ok(x, S, (pc.get("reserved") or codes)):
            fail.append([sorted(W), "tanki", x]); break
rep["elements_checked"] = tot_elems
rep["structural_failures"] = len(fail)
log("结构化全称判据: %d 元素, 失败 %d" % (tot_elems, len(fail)))
if fail: log("  失败例: %s" % fail[:6])

# ---------- 2) 手牌级模拟 ----------
stats = dict(flush=0, flush_fail=0, std=0, std_fail=0, chiitoi=0, chiitoi_fail=0,
             kokushi=0, kokushi_fail=0, no_class=0)
def sim(H):
    W = waits13(tuple(H))
    if not W: return None
    cs = class_to_codes.get(W)
    if cs is None:
        stats["no_class"] += 1; return "NO_CLASS"
    for c in cs:
        if contains(tuple(H), c): return c
    return "NO_CODE"
for combo in itertools.combinations_with_replacement(range(9), 13):
    h = [0]*9
    for x in combo: h[x] += 1
    if max(h) > 4: continue
    H = [0]*34
    for i in range(9): H[i] = h[i]
    if not waits13(tuple(H)): continue
    stats["flush"] += 1
    r = sim(H)
    if r is None or isinstance(r, str): stats["flush_fail"] += 1
log("清一色全量: %d 手, 失败 %d (未分类 %d)" % (stats["flush"], stats["flush_fail"], stats["no_class"]))
MELDS = []
for s in range(3):
    for i in range(7): MELDS.append(tuple(1 if x in (i,i+1,i+2) else 0 for x in range(9)) + (0,)*25)
for s in range(3):
    for i in range(9): MELDS.append(tuple(3 if x == i else 0 for x in range(9)) + (0,)*25)
for i in range(7): MELDS.append((0,)*27 + tuple(3 if x == i else 0 for x in range(7)))
random.seed(2024)
n_try = 0
while stats["std"] < 600000 and n_try < 4000000:
    n_try += 1
    H = [0]*34
    for _ in range(4):
        m = random.choice(MELDS)
        for i in range(34): H[i] += m[i]
    p = random.randrange(34); H[p] += 2
    if max(H) > 4: continue
    c = [i for i in range(34) if H[i] > 0]
    t = random.choice(c); H[t] -= 1
    if not waits13(tuple(H)): continue
    stats["std"] += 1
    r = sim(H)
    if r is None or isinstance(r, str): stats["std_fail"] += 1
log("随机标准型听牌: %d 手, 失败 %d" % (stats["std"], stats["std_fail"]))
while stats["chiitoi"] < 400000:
    ts = random.sample(range(34), 7)
    H = [0]*34
    for t in ts[:6]: H[t] = 2
    H[ts[6]] = 1
    if not waits13(tuple(H)): continue
    stats["chiitoi"] += 1
    r = sim(H)
    if r is None or isinstance(r, str): stats["chiitoi_fail"] += 1
log("随机七对子(6对+单张): %d 手, 失败 %d" % (stats["chiitoi"], stats["chiitoi_fail"]))
for miss in list(KOKUSHI_TILES) + [None]:
    H = [0]*34
    for t in KOKUSHI_TILES: H[t] = 1
    if miss is not None: H[miss] += 1
    stats["kokushi"] += 1
    if isinstance(sim(H), str): stats["kokushi_fail"] += 1
log("国士: %d 手, 失败 %d" % (stats["kokushi"], stats["kokushi_fail"]))
rep["hand_sim"] = stats
rep["hand_sim_total"] = stats["flush"]+stats["std"]+stats["chiitoi"]+stats["kokushi"]

# ---------- 3) 子宇宙预算(lead 引理) ----------
sub = {}
def budget_check(name, base, ntypes, limit):
    per_class_hits = {}
    for combo in itertools.combinations_with_replacement(range(ntypes), 13):
        h = [0]*ntypes
        for x in combo: h[x] += 1
        if max(h) > 4: continue
        H = [0]*34
        for i in range(ntypes): H[base+i] = h[i]
        W = waits13(tuple(H))
        if not W: continue
        cs = class_to_codes.get(W)
        if cs is None: continue
        per_class_hits.setdefault(W, []).append((H, [c for c in cs if contains(tuple(H), c)]))
    total = 0; nmiss = 0
    for W, lst in per_class_hits.items():
        # 贪心选最少码覆盖该类全部 U-手牌
        rem = list(range(len(lst))); chosen = []
        while rem:
            cnt = collections.Counter()
            for i in rem:
                for c in lst[i][1]: cnt[c] += 1
            if not cnt: nmiss += len(rem); break
            best = max(cnt, key=lambda c: cnt[c])
            chosen.append(best)
            rem = [i for i in rem if best not in lst[i][1]]
        total += len(chosen)
    sub[name] = {"sum_tau_U": total, "budget": limit, "ok": total <= limit, "classes": len(per_class_hits), "uncovered": nmiss}
    log("子宇宙 %s: Στ_U = %d <= %d ? %s (类 %d)" % (name, total, limit, total <= limit, len(per_class_hits)))
budget_check("m", 0, 9, 9**K)
budget_check("z", 27, 7, 7**K)
rep["sub_universe"] = sub
rep["ok"] = (len(fail) == 0 and rep["code_collisions"] == 0 and rep["classes_missing"] == 0
             and stats["flush_fail"] == 0 and stats["std_fail"] == 0 and stats["chiitoi_fail"] == 0
             and stats["kokushi_fail"] == 0 and all(v["ok"] for v in sub.values()))
CKP = os.path.join(OUT, "check_k%d.json" % K)
json.dump(rep, open(CKP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if K == 3:
    json.dump(rep, open(os.path.join(OUT, "check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("写出 %s ; ok=%s ; 模拟总手数 %d" % (CKP, rep["ok"], rep["hand_sim_total"]))
