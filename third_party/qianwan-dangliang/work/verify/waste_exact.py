#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""waste_exact.py <plan.json> -- 用 per-A 变体表精确计算"每类可用码集合" -> 可安全删除的浪费码.
保守化(只为安全): 惰性吸收判定忽略 chi 限制(允许任意合法 F), 因此可用码只会多判、浪费码只会少判。
输出 work/verify/waste_list_exact.json
"""
import json, sys, os, pickle, time, itertools, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "strategy"))
from indep_core import melds_only, melds_only_honor, gen_vectors
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
NM = lambda t: ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def to_idx_one(nm):
    nm = str(nm).strip()
    if nm in HON: return HON[nm]
    if nm and nm[0] in "mps": return "mps".index(nm[0]) * 9 + int(nm[1:]) - 1
    return "mps".index(nm[-1]) * 9 + int(nm[0]) - 1
def to_idx(w):
    if isinstance(w, int): return [t for t in range(34) if (w >> t) & 1]
    if w and all(isinstance(x, int) for x in w): return list(w)
    return [to_idx_one(nm) for nm in w]
CAT_BASE = (0, 9, 18, 27); CAT_LEN = (9, 9, 9, 7)
DEC = {}
def dec_vecs(ci, s):
    k = (ci, s)
    if k in DEC: return DEC[k]
    K = CAT_LEN[ci]; hon = ci == 3; off = CAT_BASE[ci]
    out = []
    for v in gen_vectors(K, s):
        if (melds_only_honor(v) if hon else melds_only(v)):
            u = [0] * 34
            for i, x in enumerate(v):
                if x: u[off + i] = x
            out.append(u)
    DEC[k] = out; return out
def absorb(inert, m, demand):
    """惰性部分 demand(34 维) 能否被 inert 花色的补牌族(每类尺寸≡0 mod 3, 可拆面子, 总 m)吸收"""
    cats = list(inert)
    def rec(i, rem, acc):
        for t in range(34):
            if demand[t] > acc[t]:
                ci = 3 if t >= 27 else t // 9
                if ci not in cats[i:]: return False
        if i == len(cats): return rem == 0
        ci = cats[i]
        for s in range(0, rem + 1, 3):
            if (rem - s) > 12 * (len(cats) - i - 1): continue
            for v in dec_vecs(ci, s):
                a2 = list(acc)
                for t, x in enumerate(v): a2[t] += x
                if rec(i + 1, rem - s, a2): return True
        return False
    return rec(0, m, [0] * 34)
plan_path = sys.argv[1] if len(sys.argv) > 1 else "work/verify/plan_k4_final.json"
P = json.load(open(plan_path, encoding="utf-8"))
plancls = {}
for r in P["plan"]:
    W = frozenset(to_idx(r["W"]))
    plancls.setdefault(W, []).extend(tuple(c) for c in r["codes"])
TC = pickle.load(open("work/strategy/out/table_cache.pkl", "rb"))
CLS = TC["cls"]; PROFI_D = TC["PROFI_D"]; PROFII_D = TC["PROFII_D"]
print("表载入: cls", len(CLS), "PROFI_D", len(PROFI_D), "PROFII_D", len(PROFII_D), flush=True)
t0 = time.time()
_act = {}; _abs = {}
def active_ok(key, demand):
    k = (key, demand)
    v = _act.get(k)
    if v is not None: return v
    entry = PROFI_D.get(key) or PROFII_D.get(key)
    if entry is None: _act[k] = False; return False
    am, xs = entry
    res = any(all(X[i] >= demand[i] for i in range(len(X))) for X in xs)
    _act[k] = res; return res
def active_vec(key, demand, ci):
    """返回 demand 在该花色内的局部形式"""
    return tuple(demand[CAT_BASE[ci]:CAT_BASE[ci] + CAT_LEN[ci]])
ORPH_T = [0, 8, 9, 17, 18, 26] + list(range(27, 34))
_KOKFAM = {}
def kok_family(W):
    """精确重建该类经 KOK 来源可得的全部手牌 (不依赖表格里那 1 条代表手牌):
       |W|=13 (13 张幺九) -> 唯一手牌 = 13 张幺九各一张;
       |W|=1  (单张幺九 t) -> 12 张其它幺九各一张 + 任取一张重复 (12 手);
       已用 indep_core.compute_W 独立验证这 12 手的 W 恰为 {t}。"""
    S = tuple(sorted(W))
    if S in _KOKFAM: return _KOKFAM[S]
    fam = []
    if len(S) == 13 and set(S) == set(ORPH_T):
        h = [0] * 34
        for o in ORPH_T: h[o] = 1
        fam.append(tuple(h))
    elif len(S) == 1 and S[0] in ORPH_T:
        t = S[0]; base = [o for o in ORPH_T if o != t]
        for d in base:
            h = [0] * 34
            for o in base: h[o] = 1
            h[d] += 1
            fam.append(tuple(h))
    else:
        raise SystemExit("意外的 KOK 类: %r" % (S,))
    _KOKFAM[S] = fam
    return fam
waste = {}; usable_cnt = 0; tot = 0
for W, cs in plancls.items():
    blocks = CLS.get(W, [])
    for c in cs:
        tot += 1
        cv = [0] * 34
        for t in c: cv[t] += 1
        ok = False
        for b in blocks:
            kind = b[0]
            if kind == "I":
                c1, s1, k1 = b[1]
                if active_ok((c1, s1, k1), active_vec((c1, s1, k1), cv, c1)):
                    inert = tuple(i for i in range(4) if i != c1)
                    dd = list(cv)
                    for i in range(CAT_BASE[c1], CAT_BASE[c1] + CAT_LEN[c1]): dd[i] = 0
                    kk = (inert, 13 - s1, tuple(dd))
                    r = _abs.get(kk)
                    if r is None:
                        r = absorb(inert, 13 - s1, dd); _abs[kk] = r
                    if r: ok = True; break
            elif kind == "II":
                c1, s1, k1 = b[1]; c2, s2, k2 = b[2]
                if active_ok((c1, s1, k1), active_vec((c1, s1, k1), cv, c1)) and \
                   active_ok((c2, s2, k2), active_vec((c2, s2, k2), cv, c2)):
                    inert = tuple(i for i in range(4) if i not in (c1, c2))
                    dd = list(cv)
                    for i in list(range(CAT_BASE[c1], CAT_BASE[c1] + CAT_LEN[c1])) + list(range(CAT_BASE[c2], CAT_BASE[c2] + CAT_LEN[c2])): dd[i] = 0
                    # 惰性需求必须落在 inert 类别内, 且能被该来源的补牌族吸收
                    if any(dd[i] for i in range(34) if (3 if i >= 27 else i // 9) not in inert):
                        continue
                    kk = (inert, 13 - s1 - s2, tuple(dd))
                    r = _abs.get(kk)
                    if r is None:
                        r = absorb(inert, 13 - s1 - s2, dd); _abs[kk] = r
                    if r: ok = True; break
            elif kind in ("KOK", "kokushi"):
                # 国士类: 该类经 KOK 来源的全部手牌 (见 kok_family); 码须 ⊆ 其中一手
                if any(all(cv[i] <= h[i] for i in range(34)) for h in kok_family(W)):
                    ok = True; break
            else:
                ok = True; break     # 其他来源(如 chiitoi)一律保守视为可用
        if ok: usable_cnt += 1
        else: waste.setdefault(tuple(NM(t) for t in sorted(W)), []).append([NM(t) for t in c])
nw = sum(len(v) for v in waste.values())
print("精确判定: 总码", tot, "可用", usable_cnt, "**可安全删除的浪费码**", nw, "涉及类", len(waste), "(%.0fs)" % (time.time() - t0))
# ---- 200 条独立复核: 对每条待删码, 从该类来源随机造 3000 手牌, 确认没有一手装得下它 ----
import random as _rnd
rng = _rnd.Random(20260917)
flat = [(Wn, cc) for Wn, lst in waste.items() for cc in lst]
sample = rng.sample(flat, min(200, len(flat)))
false_pos = []
for Wn, cc in sample:
    W = frozenset(to_idx_one(x) for x in Wn)
    cidx = [to_idx_one(x) for x in cc]
    cv = [0] * 34
    for t in cidx: cv[t] += 1
    hands = []
    for b in CLS.get(W, []):
        if b[0] == "I":
            key = b[1]; entry = PROFI_D.get(key)
            if not entry: continue
            am, xs = entry
            inert = [i for i in range(4) if i != key[0]]; m = 13 - key[1]
            for _ in range(20):
                X = rng.choice(xs); A = [0] * 34
                for i, x in enumerate(X): A[CAT_BASE[key[0]] + i] = x
                rem = m
                for ii, ci in enumerate(inert):
                    left = len(inert) - ii - 1
                    opts = [s2 for s2 in range(0, rem + 1, 3) if rem - s2 <= 12 * left and (s2 == 0 or dec_vecs(ci, s2))]
                    if not opts: rem = -1; break
                    s2 = rng.choice(opts)
                    if s2:
                        v = rng.choice(dec_vecs(ci, s2))
                        for i, x in enumerate(v): A[i] += x
                    rem -= s2
                if rem == 0: hands.append(A)
        elif b[0] in ("KOK", "kokushi"):
            for h in kok_family(W): hands.append(list(h))
        elif b[0] == "II":
            k1, k2 = b[1], b[2]
            e1, e2 = PROFII_D.get(k1), PROFII_D.get(k2)
            if not e1 or not e2: continue
            inert = [i for i in range(4) if i not in (k1[0], k2[0])]; m = 13 - k1[1] - k2[1]
            for _ in range(20):
                X1 = rng.choice(e1[1]); X2 = rng.choice(e2[1]); A = [0] * 34
                for i, x in enumerate(X1): A[CAT_BASE[k1[0]] + i] = x
                for i, x in enumerate(X2): A[CAT_BASE[k2[0]] + i] = x
                rem = m
                for ii, ci in enumerate(inert):
                    left = len(inert) - ii - 1
                    opts = [s2 for s2 in range(0, rem + 1, 3) if rem - s2 <= 12 * left and (s2 == 0 or dec_vecs(ci, s2))]
                    if not opts: rem = -1; break
                    s2 = rng.choice(opts)
                    if s2:
                        v = rng.choice(dec_vecs(ci, s2))
                        for i, x in enumerate(v): A[i] += x
                    rem -= s2
                if rem == 0: hands.append(A)
    bad = [h for h in hands if all(h[t] >= cv[t] for t in range(34))] if hands else []
    if bad: false_pos.append({"W": list(Wn), "code": list(cc), "hand": bad[0], "n_hands": len(hands)})
print("200 条独立复核: 误报", len(false_pos), "/", len(sample))
out = {"plan": plan_path, "total_codes": tot, "usable": usable_cnt, "waste_count": nw,
       "waste_by_class": [{"W": list(k), "codes": v} for k, v in waste.items()],
       "audit": {"sampled": len(sample), "false_positives": len(false_pos), "examples": false_pos[:5]}}
OUTP = sys.argv[2] if len(sys.argv) > 2 else "waste_list_exact.json"
json.dump(out, open(OUTP if os.path.isabs(OUTP) else os.path.join(HERE, OUTP), "w"), ensure_ascii=False, indent=1)
print("已写", OUTP)
