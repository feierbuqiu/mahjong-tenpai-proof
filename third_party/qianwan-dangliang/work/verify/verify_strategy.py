#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T6b: 独立复核 T4 的 k=3 策略 (plan.json: 类 -> 码).
检查:
  A 类集合完整性 / 码合法性 / 全局码不交
  B Type I 来源块的**完备**覆盖 (DFS 枚举整个补牌族 F)
  C Type II 块的通用码条件 (码 ⊆ min(A1)+min(A2))
  D 子宇宙完备检查: 全部单类别手牌 (m/p/s 各 93,600, z 7,875) 的覆盖 + 反向解码
  E chiitoi 覆盖 (组合论证: 6 对 + 单张 z)
  F 国士手牌覆盖
  G >=10^6 手蒙特卡洛: 结构化抽样, 覆盖 + 解码一致性(反向证伪)
"""
import json, sys, itertools, random, time
from collections import defaultdict, Counter
sys.path.insert(0, "work/verify")
from indep_core import (compute_W, closed_form_W, gen_vectors, melds_only,
                        melds_only_honor, CAP, KOKUSHI_IDX)

CAT_K = (9, 9, 9, 7); CAT_HON = (False, False, False, True); CAT_OFF = (0, 9, 18, 27)
CAT_NAME = ("m", "p", "s", "z"); SUIT_IDX = {"m": 0, "p": 1, "s": 2, "z": 3}
T0 = time.time()
def log(*a): print("[%6.1fs]" % (time.time() - T0), *a, flush=True)

PLAN_PATH = sys.argv[2] if len(sys.argv) > 2 else "work/strategy/out/plan.json"
plan = json.load(open(PLAN_PATH, encoding="utf-8"))
if isinstance(plan, list): plan = {"k": 3, "plan": plan, "fails": []}

_HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
def _to_idx(w):
    """W 可能是 [牌索引] / [牌名] / Wmask(int)"""
    if isinstance(w, int):
        return [t for t in range(34) if (w >> t) & 1]
    out = []
    for nm in w:
        if isinstance(nm, int): out.append(nm)
        elif nm in _HON: out.append(_HON[nm])
        else: out.append(("mps".index(nm[-1])) * 9 + int(nm[0]) - 1)
    return out

_rows = plan["plan"]
plan["plan"] = [{"W": _to_idx(r["W"]), "codes": r["codes"]} for r in _rows]
g = json.load(open("work/data/out/global.json", encoding="utf-8"))
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
plancls = {}
for r in plan["plan"]:
    # 码是【有序】k 元组: 不同排列算不同码; 覆盖判断用其多重集
    plancls[frozenset(r["W"])] = [tuple(c) for c in r["codes"]]

K_PLAN = plan.get("k", 3)
rep = {"k": plan["k"], "plan_classes": len(plancls),
       "plan_codes": sum(len(v) for v in plancls.values()), "plan_fails": len(plan.get("fails", [])),
       "census_classes": len(mine),
       "classes_missing_in_plan": len(mine - set(plancls)),
       "classes_extra_in_plan": len(set(plancls) - mine),
       "missing_examples": [sorted(x) for x in list(mine - set(plancls))[:5]],
       "extra_examples": [sorted(x) for x in list(set(plancls) - mine)[:5]]}
log("plan k=%s classes=%s codes=%s" % (rep["k"], rep["plan_classes"], rep["plan_codes"]))

# --- A 码合法性 + 全局不交 ---
owner = {}; invalid = []; coll = []
for W, cs in plancls.items():
    for c in cs:
        if len(c) != K_PLAN or any(c.count(t) > CAP for t in set(c)): invalid.append((sorted(W), c))
        if c in owner and owner[c] != W: coll.append((c, sorted(owner[c]), sorted(W)))
        owner[c] = W
rep["plan_path"] = PLAN_PATH
rep["zero_code_classes"] = sum(1 for cs in plancls.values() if not cs)
rep["min_distinct_codes_needed"] = len(mine)
rep["invalid_codes"] = len(invalid); rep["invalid_examples"] = invalid[:5]
rep["code_collisions"] = len(coll); rep["collision_examples"] = [(list(c), a, b) for c, a, b in coll[:5]]
rep["distinct_codes"] = len(owner)
rep["max_ordered_code_reuse"] = max((sum(1 for cs in plancls.values() for c in cs if c == k) for k in list(owner)[:1]), default=0)
multisets = Counter(tuple(sorted(c)) for cs in plancls.values() for c in cs)
def _perms(m):
    return 1 if len(set(m)) == 1 else (3 if len(set(m)) == 2 else 6)
rep["multisets_over_perm_capacity"] = sum(1 for m, k in multisets.items() if k > _perms(m))
rep["distinct_codes_ok"] = True  # 有序码空间足够 (34^3), 关键是"同一有序码不得两类共用"
log("distinct codes %d collisions %d invalid %d zero-code classes %d" % (
    len(owner), len(coll), len(invalid), rep["zero_code_classes"]))

# --- helpers ---
DEC = {}
def dec_vecs(ci, s):
    key = (ci, s)
    if key in DEC: return DEC[key]
    K = CAT_K[ci]; hon = CAT_HON[ci]; off = CAT_OFF[ci]
    out = []
    for v in gen_vectors(K, s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u = [0] * 34
            for i, x in enumerate(v):
                if x: u[off + i] = x
            out.append(tuple(u))
    DEC[key] = out
    return out

def contains(hand, c):
    need = {}
    for t in c: need[t] = need.get(t, 0) + 1
    for t, v in need.items():
        if hand[t] < v: return False
    return True

def parse_digits(s, ci):
    off = CAT_OFF[ci]
    u = [0] * 34
    for i, ch in enumerate(s):
        if ch != "0": u[off + i] = int(ch)
    return u

def add_into(u, v):
    for i, x in enumerate(v):
        if x: u[i] += x
    return u

# --- B Type I 块完备覆盖 ---
NODE_CAP = 3000000
def typeI_covered(A, inert, m, codes):
    if any(contains(A, c) for c in codes): return True, None, 0
    inert_idx = [SUIT_IDX[x] for x in inert]
    nodes = [0]; over = [False]
    def rec(i, rem, hand):
        nodes[0] += 1
        if nodes[0] > NODE_CAP: over[0] = True; return True
        for c in codes:
            if contains(hand, c): return True      # 部分手牌已含某码 => 所有扩展都被覆盖
        if i == len(inert_idx):
            return rem != 0                        # rem==0 且无码 => 找到未覆盖手牌
        ci = inert_idx[i]
        for s in range(0, rem + 1, 3):
            if (rem - s) > 3 * 4 * (len(inert_idx) - i - 1): continue
            for v in dec_vecs(ci, s):
                h2 = list(hand); add_into(h2, v)
                if not rec(i + 1, rem - s, h2): return False   # 任一扩展未覆盖 => 块未覆盖
        return True
    r = rec(0, m, list(A))
    if over[0]: return None, None, nodes[0]
    return (r is True), r, nodes[0]

# --- C/E/F: 逐来源检查 ---
rep["source_checks"] = {"typeI_blocks": 0, "typeI_uncovered": [], "typeI_over_budget": 0,
                        "typeII_blocks": 0, "typeII_without_universal": [],
                        "kokushi_ok": None, "chiitoi_bad": []}
for row in g["classes"]:
    W = frozenset(t for t in (0,))
    # 用牌名映射成索引
    name2idx = {}
    for nm in row["W"]:
        if nm[-1] in SUIT_IDX and nm[-1] != "z": name2idx[nm] = SUIT_IDX[nm[-1]] * 9 + int(nm[0]) - 1
        else: name2idx[nm] = 27 + {"E": 0, "S": 1, "W": 2, "N": 3, "Haku": 4, "Hatsu": 5, "Chun": 6}[nm]
    W = frozenset(name2idx[nm] for nm in row["W"])
    if W not in plancls: continue
    codes = plancls[W]
    srcs = row.get("sources", [])
    if not any(s["kind"] == "kokushi" for s in srcs):
        for s in srcs:
            if s["kind"] == "I":
                rep["source_checks"]["typeI_blocks"] += 1
                ci = SUIT_IDX[s["cat"]]; A = parse_digits(s["A"], ci)
                m = 13 - sum(A)
                ok, wit, nodes = typeI_covered(A, s["inert"], m, codes)
                if ok is None:
                    rep["source_checks"]["typeI_over_budget"] += 1
                elif not ok:
                    rep["source_checks"]["typeI_uncovered"].append(
                        {"W": sorted(W), "A": s["A"], "cat": s["cat"], "m": m, "nF": s["nF"]})
            elif s["kind"] == "II":
                rep["source_checks"]["typeII_blocks"] += 1
                inter = [0] * 34
                for nm, ds in (("A1", s.get("minA1")), ("A2", s.get("minA2"))):
                    if ds is None: continue
                    # 数字串长度 = 该类别长度, 需知道是哪个类别
                # 直接按数字串长度定位类别
                offs = []
                for key, ds in (("minA1", s.get("minA1")), ("minA2", s.get("minA2"))):
                    if ds is None: continue
                    L = len(ds)
                    ci = {9: None, 7: 3}.get(L)
                    if L == 9:
                        # 由 cats 顺序推断
                        ci = SUIT_IDX[s["cats"][0 if key == "minA1" else 1]]
                    u = parse_digits(ds, ci)
                    add_into(inter, u)
                if not any(contains(inter, c) for c in codes):
                    rep["source_checks"]["typeII_without_universal"].append(
                        {"W": sorted(W), "cats": s["cats"], "inert": s["inert"], "nF": s["nF"], "nA": s.get("nA")})
    else:
        # 国士
        hand = [0] * 34
        for t in KOKUSHI_IDX: hand[t] = 1
        # 12 distinct + 1 duplicate: 检查两种
        ok1 = any(contains(hand, c) for c in codes)
        dup = False
        for t in KOKUSHI_IDX:
            h2 = list(hand); h2[t] += 1
            if not any(contains(h2, c) for c in codes): dup = True
        rep["source_checks"]["kokushi_ok"] = bool(ok1 and not dup)

# --- E chiitoi: 该类的 6 对 + 单张 z 手牌覆盖 ---
def chiitoi_covered(z, codes):
    # 找 6 元子集 K (不含 z) 使没有任何 code 满足: 非 z 牌都在 K 内且 z 计数<=1
    others = [t for t in range(34) if t != z]
    forb = {}
    # 严格七对子手牌 = 6 对 + 单张 z: 每牌最多 2 张, z 最多 1 张
    # 因此含非 z 牌 >=3 张、或 z >=2 张的码永远装不进这类手牌 => 剔除
    zcodes = [c for c in codes if c.count(z) <= 1 and all(c.count(t) <= 2 for t in set(c) if t != z)]
    if not zcodes: return False, None
    single_forbid = set()
    hyper = []
    for c in zcodes:
        rest = [t for t in c if t != z]
        R = frozenset(rest)
        if len(R) == 0:
            return True, None   # 码 = (z,z,z)? 不可能; 但 (z) 单独不算
        if len(R) == 1: single_forbid |= R
        else: hyper.append(R)
    allowed = [t for t in others if t not in single_forbid]
    # 找 size 6 的独立集 (不含任何 hyper 超边)
    hyp_by_size = defaultdict(list)
    for R in hyper: hyp_by_size[len(R)].append(R)
    def independent(K):
        Ks = set(K)
        for R in hyper:
            if R <= Ks: return False
        return True
    found = None
    def rec(start, K):
        nonlocal found
        if found is not None: return
        if len(K) == 6:
            if independent(K): found = list(K)
            return
        if len(allowed) - start < 6 - len(K): return
        for i in range(start, len(allowed)):
            K.append(allowed[i])
            rec(i + 1, K)
            K.pop()
            if found is not None: return
    rec(0, [])
    return (found is None), found

# chiitoi 手牌级抽样 (正确做法: 每个 6 对+单张手牌先算 W 再查该类码)
import random as _rnd
_rng = _rnd.Random(777)
_chi_n = 0; _chi_zero = 0; _chi_fail = []; _chi_cov_n = 0
for _ in range(200000):
    z = _rng.randrange(34)
    others = [t for t in range(34) if t != z]
    K = _rng.sample(others, 6)
    hand = [0] * 34
    for t in K: hand[t] = 2
    hand[z] = 1
    W = closed_form_W(hand)
    if not W: continue
    _chi_n += 1
    cs = plancls.get(W)
    if not cs:
        _chi_zero += 1
        if len(_chi_fail) < 5: _chi_fail.append({"kind": "zero-code", "W": sorted(W), "hand": hand})
        continue
    if not any(contains(hand, c) for c in cs):
        _chi_cov_n += 1
        if len(_chi_fail) < 5: _chi_fail.append({"kind": "coverage", "W": sorted(W), "hand": hand, "codes": [list(c) for c in cs]})
rep["source_checks"]["chiitoi_hand_samples"] = _chi_n
rep["source_checks"]["chiitoi_zero_code"] = _chi_zero
rep["source_checks"]["chiitoi_fail_examples"] = _chi_fail
rep["source_checks"]["chiitoi_fail_n"] = _chi_cov_n
rep["source_checks"]["chiitoi_bad"] = _chi_fail
rep["source_checks"]["typeI_uncovered_n"] = len(rep["source_checks"]["typeI_uncovered"])
rep["source_checks"]["typeI_uncovered"] = rep["source_checks"]["typeI_uncovered"][:5]
rep["source_checks"]["typeII_without_universal_n"] = len(rep["source_checks"]["typeII_without_universal"])
rep["source_checks"]["typeII_without_universal"] = rep["source_checks"]["typeII_without_universal"][:5]
log("source checks done: typeI blocks=%d uncovered=%d budget=%d typeII=%d no_universal=%d chiitoi_fail=%s kokushi=%s" % (
    rep["source_checks"]["typeI_blocks"], rep["source_checks"]["typeI_uncovered_n"],
    rep["source_checks"]["typeI_over_budget"], rep["source_checks"]["typeII_blocks"],
    rep["source_checks"]["typeII_without_universal_n"], len(rep["source_checks"]["chiitoi_bad"]),
    rep["source_checks"]["kokushi_ok"]))

# --- D 子宇宙完备: 全部单类别手牌 ---
def subuniverse_check():
    res = {}
    for ci, name in ((0, "m"), (1, "p"), (2, "s"), (3, "z")):
        K = CAT_K[ci]; off = CAT_OFF[ci]
        codes_here = {}   # 只用落在该门的码 (有序码)
        for W, cs in plancls.items():
            for c in cs:
                if all(off <= t < off + K for t in c):
                    codes_here[c] = W
        def owner_of_multiset(comb):
            for pm in set(itertools.permutations(comb)):
                w = codes_here.get(pm)
                if w is not None: return w
            return None
        cov_fail = []; snd_fail = []; nhands = 0; nlisten = 0
        for h in gen_vectors(K, 13):
            c = [0] * 34
            for i, x in enumerate(h):
                if x: c[off + i] = x
            W = compute_W(c)
            if not W: continue
            nlisten += 1
            nhands += 1
            cs = plancls.get(frozenset(W))
            if cs is None or not any(contains(c, code) for code in cs):
                if len(cov_fail) < 5: cov_fail.append({"W": sorted(W), "hand": list(h)})
            # 反向: 所有能装进本手的、属于别的类的码
            tiles = [t for t in range(off, off + K) if c[t] > 0]
            for comb in itertools.combinations_with_replacement(tiles, 3):
                w2 = owner_of_multiset(comb)
                if w2 is not None and w2 != frozenset(W):
                    if len(snd_fail) < 5: snd_fail.append({"code": sorted(comb), "decodes_to": sorted(w2), "hand_W": sorted(W)})
        res[name] = {"listening_hands": nlisten, "coverage_fail": len(cov_fail), "soundness_fail": len(snd_fail),
                     "coverage_examples": cov_fail, "soundness_examples": snd_fail}
        log("sub-universe %s: hands=%d coverage_fail=%d soundness_fail=%d" % (name, nlisten, len(cov_fail), len(snd_fail)))
    return res

rep["sub_universe"] = subuniverse_check()

# --- G 蒙特卡洛: 结构化抽样 ---
rng = random.Random(20260915)
FAMS = {}
def fam_vectors(ci, s): return dec_vecs(ci, s)
def rand_vec(ci, n):
    K = CAT_K[ci]; c = [0] * K
    for _ in range(n):
        while True:
            t = rng.randrange(K)
            if c[t] < CAP: c[t] += 1; break
    return c
def rand_F(cats, m):
    hand = [0] * 34
    rem = m
    for idx, ci in enumerate(cats):
        left = len(cats) - idx - 1
        choices = [s for s in range(0, rem + 1, 3) if rem - s <= 3 * 4 * left and (s == 0 or dec_vecs(ci, s))]
        s = rng.choice(choices)
        if s:
            v = rng.choice(dec_vecs(ci, s)); add_into(hand, v)
        rem -= s
    return hand

def rand_hand():
    t = rng.random()
    hand = [0] * 34
    if t < 0.30:
        ci = rng.randrange(4); n = rng.choice([1, 4, 7, 10, 13])
        X = rand_vec(ci, n); add_into(hand, [x if i >= CAT_OFF[ci] and i < CAT_OFF[ci] + CAT_K[ci] else 0 for i, x in enumerate([0] * 34)])
        for i, x in enumerate(X): hand[CAT_OFF[ci] + i] += x
        others = [c for c in range(4) if c != ci]
        add_into(hand, rand_F(others, 13 - n))
    elif t < 0.75:
        c1, c2 = rng.sample(range(4), 2)
        n1 = rng.choice([2, 5, 8, 11]); n2 = rng.choice([2, 5, 8, 11])
        if n1 + n2 > 13: n1, n2 = 2, 2
        X1 = rand_vec(c1, n1); X2 = rand_vec(c2, n2)
        for i, x in enumerate(X1): hand[CAT_OFF[c1] + i] += x
        for i, x in enumerate(X2): hand[CAT_OFF[c2] + i] += x
        others = [c for c in range(4) if c not in (c1, c2)]
        add_into(hand, rand_F(others, 13 - n1 - n2))
    elif t < 0.92:
        kinds = rng.sample(range(34), 7)
        z = rng.choice(kinds)
        for k in kinds: hand[k] = 2
        hand[z] = 1
    elif t < 0.96:
        ks = rng.sample(KOKUSHI_IDX, 12)
        for k in ks: hand[k] = 1
        hand[rng.choice(ks)] += 1
    else:
        for _ in range(13):
            while True:
                x = rng.randrange(34)
                if hand[x] < CAP: hand[x] += 1; break
    return hand

N_SIM = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
nlisten = 0; cov_fail = []; snd_fail = []; class_hits = set(); bf_check = 0; bf_fail = 0
codes_by_sig = {}
for W, cs in plancls.items():
    codes_by_sig[W] = cs
for it in range(N_SIM):
    h = rand_hand()
    W = closed_form_W(h)
    if not W: continue
    nlisten += 1
    class_hits.add(W)
    cs = plancls.get(W)
    if cs is None or not any(contains(h, c) for c in cs):
        if len(cov_fail) < 8: cov_fail.append({"hand": h, "W": sorted(W)})
    if it % 8 == 0:
        for comb in itertools.combinations_with_replacement([t for t in range(34) if h[t] > 0], 3):
            for pm in set(itertools.permutations(comb)):
                w2 = owner.get(pm)
                if w2 is not None and w2 != W:
                    if len(snd_fail) < 8: snd_fail.append({"code": list(pm), "decodes_to": sorted(w2), "hand_W": sorted(W), "hand": h})
                    break
    if it % 2000 == 0:
        bf = compute_W(h); bf_check += 1
        if bf != W: bf_fail += 1
    if it % 100000 == 0:
        log("sim %d listening=%d classes_hit=%d cov_fail=%d snd_fail=%d" % (it, nlisten, len(class_hits), len(cov_fail), len(snd_fail)))
rep["simulation"] = {"samples": N_SIM, "listening": nlisten, "classes_hit": len(class_hits),
                     "coverage_fail": len(cov_fail), "coverage_examples": cov_fail,
                     "soundness_fail": len(snd_fail), "soundness_examples": snd_fail,
                     "bruteforce_checked": bf_check, "bruteforce_mismatch": bf_fail}
rep["elapsed"] = round(time.time() - T0, 1)
json.dump(rep, open("work/verify/verify_report.json", "w"), ensure_ascii=False, indent=1)
log("DONE", json.dumps({k: v for k, v in rep.items() if k not in ("sub_universe", "simulation", "source_checks")}, ensure_ascii=False))
