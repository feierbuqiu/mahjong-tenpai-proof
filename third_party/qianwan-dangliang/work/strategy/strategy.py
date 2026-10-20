# -*- coding: utf-8 -*-
"""strategy.py -- k=3 显式构造(A 摆放 + B 解码表), 严格七对子口径。
覆盖模型:
  普通块 |A|>=3: 码 c 对来源 A 通用 <=> multiset(c) ⊆ A
  Type II 块: s>=3 的一侧整体覆盖(码落在该侧花色内); 仅 s1=s2=2 时枚举对
  tanki 块(A={x}): 码族 {(x,a,a)} ∪ {(x,a,a+1)}  (34 个单元素类)
  纯七对子手牌(6 对+单张 z): 码族 {(z,a,a)}, a 取遍 33 种
"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
K = int(os.environ.get("STRAT_K", "3"))
CAP = 4
KSC = {}
def ksubs(vec):
    r = KSC.get(vec)
    if r is not None: return r
    tiles = []
    for i, n in enumerate(vec): tiles.extend([i]*n)
    out = set()
    for combo in itertools.combinations_with_replacement(tiles, K):
        need = {}
        for x in combo: need[x] = need.get(x, 0)+1
        if all(vec[x] >= v for x, v in need.items()): out.add(combo)
    KSC[vec] = out
    return out
def perm_count(m):
    from math import factorial
    d = 1
    for x in set(m): d *= factorial(m.count(x))
    return factorial(len(m))//d
def vec_of(c, X):
    v = [0]*34
    for i, x in enumerate(X): v[CAT_BASE[c]+i] = x
    return tuple(v)
LAM = 0.0
def greedy_elems(keys, cands, blocked, usage=None, lam=None):
    lam = LAM if lam is None else lam
    u = usage or {}
    cnt = {}; owner = {}
    for i, k in enumerate(keys):
        for m in cands[i]:
            if m in blocked: continue
            cnt[m] = cnt.get(m, 0)+1
            owner.setdefault(m, []).append(i)
    unc = set(range(len(keys))); chosen = []
    while unc:
        best = None; bs = None
        for m, c in cnt.items():
            if c <= 0: continue
            s = c - lam*u.get(m, 0)
            if bs is None or s > bs: bs = s; best = m
        if best is None or bs is None: break
        chosen.append(best)
        for i in owner[best]:
            if i in unc:
                unc.discard(i)
                for m in cands[i]:
                    if m in cnt: cnt[m] = cnt[m]-1
    return chosen, unc
def tanki_patterns(x, S):
    """A={x}: 覆盖整个补牌族(每个 F 含一个面子).
       K=3: 刻子 aaa -> (x,a,a); 顺子 abc -> (x,a,b).
       K=4: 刻子 -> (x,a,a,a); 顺子 -> (x,a,b,c)."""
    out = set()
    if K == 3:
        for a in range(34):
            if a != x and cat_of(a) in S: out.add(tuple(sorted((x, a, a))))
        for a in range(27):
            if a % 9 < 7 and cat_of(a) in S: out.add(tuple(sorted((x, a, a+1))))
    else:
        for a in range(34):
            if a != x and cat_of(a) in S: out.add(tuple(sorted((x, a, a, a))))
        for a in range(27):
            if a % 9 < 7 and cat_of(a) in S: out.add(tuple(sorted((x, a, a+1, a+2))))
    return out
def chiitoi_patterns(z):
    """纯七对子手牌 = 6 对 + 单张 z.
       K=3: (z,a,a) 命中含对子 a 的手牌 => 取遍 33 种 a.
       K=4: (z,a,a,b) 需手牌同时含对子 a,b => 用"独立数<=5"的 2-子集族:
            33 种牌分 5 组(7,7,7,6,6), 组内两两连边 => 任意 6 对必含一条边(93 条)."""
    if K == 3:
        return {tuple(sorted((z, a, a))) for a in range(34) if a != z}
    tiles = [t for t in range(34) if t != z]
    out = set(); i = 0
    for sz in (7, 7, 7, 6, 6):
        grp = tiles[i:i+sz]; i += sz
        for p in range(len(grp)):
            for q in range(p+1, len(grp)):
                out.add(tuple(sorted((z, grp[p], grp[p], grp[q]))))
    return out

ELCACHE = {}
def class_elements(T, W, blocks):
    """返回 (ks, cands, modes): 去重后的元素与候选码"""
    ck = id(blocks)
    if ck in ELCACHE: return ELCACHE[ck]
    ed = {}; modes = []
    for b in blocks:
        kind = b[0]
        if kind == "KOK":
            H = tuple(b[1]); modes.append(("hand", None))
            ed.setdefault(("hand", H), set(ksubs(H)))
        elif kind == "I":
            (c, s, pkey) = b[1]
            am, xs = T["PROFI_D"][(c, s, pkey)]
            if s == 1:
                modes.append(("tanki", c))
            else:
                modes.append(("xset", c))
                for X in xs:
                    v = vec_of(c, X)
                    if ("A", v) not in ed: ed[("A", v)] = set(ksubs(v))
        else:
            (c1, s1, k1) = b[1]; (c2, s2, k2) = b[2]
            am1, xs1 = T["PROFII_D"][(c1, s1, k1)]; am2, xs2 = T["PROFII_D"][(c2, s2, k2)]
            if s1 >= K and s2 >= K:
                if len(xs1) <= len(xs2): modes.append(("side1", c1)); use = (c1, xs1)
                else: modes.append(("side2", c2)); use = (c2, xs2)
            elif s1 >= K: modes.append(("side1", c1)); use = (c1, xs1)
            elif s2 >= K: modes.append(("side2", c2)); use = (c2, xs2)
            else:
                modes.append(("pairs", (c1, c2))); use = None
                for X1 in xs1:
                    v1 = vec_of(c1, X1)
                    for X2 in xs2:
                        v = tuple(a+b for a, b in zip(v1, vec_of(c2, X2)))
                        if ("A", v) not in ed: ed[("A", v)] = set(ksubs(v))
            if use is not None:
                cu, xu = use
                for X in xu:
                    v = vec_of(cu, X)
                    if ("S", cu, v) not in ed: ed[("S", cu, v)] = set(ksubs(v))
    keys = list(ed.keys())
    cands = [ed[k] for k in keys]
    ELCACHE[ck] = (keys, cands, modes)
    return keys, cands, modes

def build_plan():
    import pickle, collections
    T = TL.build()
    CLS = T["cls"]
    log("类数 = %d" % len(CLS))
    INFOP = os.path.join(OUT, "elements_k%d.pkl" % K)
    INFO = None
    if os.path.exists(INFOP):
        try:
            INFO = pickle.load(open(INFOP, "rb"))
            if len(INFO) != len(CLS): INFO = None
        except Exception:
            INFO = None
    if INFO is None:
        INFO = {}
        for W, blocks in CLS.items():
            keys, cands, modes = class_elements(T, W, blocks)
            INFO[W] = (keys, cands, modes)
        pickle.dump(INFO, open(INFOP, "wb"))
    log("元素统计: Σ elements = %d, 最大 %d" % (sum(len(v[0]) for v in INFO.values()),
                                             max(len(v[0]) for v in INFO.values())))
    def cats_of_class(W):
        cats = set()
        for key in INFO[W][0]:
            if key[0] == "hand":
                v = key[1]
            elif key[0] == "S":
                v = key[2]
            else:
                v = key[1]
            for i, n in enumerate(v):
                if n: cats.add(cat_of(i))
        return cats
    CATS = {W: cats_of_class(W) for W in CLS}
    order = sorted(CLS.keys(), key=lambda W: (0 if len(CATS[W]) <= 1 else 1, len(INFO[W][0]), len(W)))
    def reserved_of(W):
        if len(W) != 1: return []
        z = next(iter(W))
        S = tuple(x for x in range(4) if x != cat_of(z))
        return sorted(tanki_patterns(z, S) | chiitoi_patterns(z))
    # 类的"公共码"容量向量 cap(W) = 各块 cap 逐牌最小; sum(cap) >= K 时一条码即可覆盖全类
    CAPOF = {}
    for W, blocks in CLS.items():
        u = [CAP]*34
        for b in blocks:
            cv = b[5]
            for i in range(34):
                if cv[i] < u[i]: u[i] = cv[i]
        CAPOF[W] = tuple(u)
    covers = {}; fails = []
    usage = collections.Counter()
    ovf = 0; ncap = 0
    # ---------- 阶段 0: 采用 lead 给出的单类别类(本门码)覆盖, 固定不改 ----------
    LEAD = {}
    _lp = os.environ.get("LEAD_COVERS")
    if _lp and os.path.exists(_lp):
        import json as _json
        _NMAP = {tile_name(t): t for t in range(34)}
        _NMAP.update({"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33})
        _used_ord = set()
        _ALL = {}
        for _f in _lp.split(";"):
            if not _f or not os.path.exists(_f): continue
            _ALL.update(_json.load(open(_f, encoding="utf-8")))
        _L = _ALL
        for _k, _v in _L.items():
            W = frozenset(_NMAP[x] for x in _v["W"])
            if W not in CLS: continue
            cds = []
            for c in _v["codes"]:
                c = tuple(sorted(c))
                if c in _used_ord:
                    alt = [p for p in itertools.permutations(c) if p not in _used_ord]
                    if not alt: continue
                    c2 = alt[0]
                    _used_ord.add(c2); cds.append(c)
                else:
                    _used_ord.add(c); cds.append(c)
            LEAD[W] = sorted(set(cds))
        log("阶段0: 采用 lead %d 个单类别类覆盖, %d 条码" % (len(LEAD), sum(len(v) for v in LEAD.values())))
        for W, cs in LEAD.items():
            covers[W] = sorted(set(cs) | set(reserved_of(W)))
            for m in covers[W]: usage[m] += 1
    # ---------- 阶段 1: 有公共码的类 -> b-容量二分匹配 (Kuhn 增广) ----------
    capclasses = [W for W in order if sum(CAPOF[W]) >= K and W not in LEAD]
    noncap = [W for W in order if sum(CAPOF[W]) < K and W not in LEAD]
    match_of = {}
    CANDCAP = {W: sorted(ksubs(CAPOF[W])) for W in capclasses}
    def kuhn(W, visited):
        for m in CANDCAP[W]:
            if m in visited: continue
            visited.add(m)
            occ = match_of.get(m, [])
            if len(occ) < perm_count(m):
                match_of.setdefault(m, []).append(W); return True
            for W2 in list(occ):
                if kuhn(W2, visited):
                    occ.remove(W2); match_of[m] = occ
                    match_of.setdefault(m, []).append(W); return True
        return False
    for W in capclasses:
        if not kuhn(W, set()):
            noncap.append(W)
    inv = {}
    for m, occ in match_of.items():
        for W in occ: inv[W] = m
        usage[m] += len(occ)
    log("阶段1 匹配: %d/%d 类拿到公共码, 用码 %d" % (len(inv), len(capclasses), sum(len(v) for v in match_of.values())))
    # ---------- 阶段 2: 其余类 -> 带容量阻塞的贪心覆盖 ----------
    # 先把"单类别元素"(只能在本身花色码池内解决)全部覆盖, 再处理混合元素,
    # 避免混合元素抢走 m/p/s 的码池导致单类别元素无码可用。
    def support(key):
        v = key[1] if key[0] != "S" else key[2]
        return {cat_of(i) for i, n in enumerate(v) if n}
    for stage in (0, 1):
        for W in noncap:
            keys, cands, modes = INFO[W]
            if stage == 0:
                sel = [i for i, k in enumerate(keys) if len(support(k)) <= 1]
            else:
                sel = [i for i, k in enumerate(keys) if len(support(k)) > 1]
            if not sel: continue
            sk = [keys[i] for i in sel]
            # 优先只使用"三张不同牌"的码(容量 6), 减少饱和; 无此类码的元素回退到全候选
            sc = []
            for i in sel:
                c = cands[i]
                d = [m for m in c if m[0] != m[1] and m[1] != m[2]]
                sc.append(d if d else list(c))
            blocked = frozenset(m for m, u in usage.items() if u >= perm_count(m))
            ch, unc = greedy_elems(sk, sc, blocked)
            if unc:
                for j in sorted(unc):
                    if not sc[j]: continue
                    free = [m for m in sc[j] if usage.get(m, 0) < perm_count(m)]
                    pool = free if free else sc[j]
                    ch.append(min(pool, key=lambda m: (usage.get(m, 0), m)))
            covers[W] = sorted(set(covers.get(W, set(reserved_of(W)))) | set(ch))
            for m in sorted(set(ch)):
                usage[m] += 1
                if usage[m] > perm_count(m): ovf += 1
            if any(not sc[j] for j in unc): fails.append((sorted(W), "no-cand")); continue
    for W, m in inv.items():
        covers[W] = sorted(set([m]) | set(reserved_of(W)))
        for x in covers[W]:
            if x != m: usage[x] += 1
        if [x for x in covers[W] if usage.get(x, 0) > perm_count(x)]: ovf += 1
    nbad = sum(1 for m, u in usage.items() if u > perm_count(m))
    log("阶段2 完成: 覆盖 %d 类, Σ|S_C| = %d, 超容量多重集 %d, 失败 %d" % (
        len(covers), sum(len(v) for v in covers.values()), nbad, len(fails)))
    nbad = sum(1 for m, u in usage.items() if u > perm_count(m))
    log("顺序装包: 成功 %d, 失败 %d, Σ|S_C| = %d, 不同多重集 %d, 超容量类 %d, 超容量多重集 %d" % (
        len(covers), len(fails), sum(len(v) for v in covers.values()), len(usage), ovf, nbad))
    # ---------- 阶段 3: 真实用量校验 + 覆盖完整化 + 驱逐修复 ----------
    def cover_with(W, blocked):
        keys, cands, modes = INFO[W]
        acc = set(reserved_of(W))
        unc_all = set()
        for stage in (0, 1):
            sel = [i for i, k in enumerate(keys) if (len(support(k)) <= 1) == (stage == 0)]
            if not sel: continue
            sk = [keys[i] for i in sel]; sc = []
            for i in sel:
                c = cands[i]
                filt = [m for m in c if m not in blocked and m[0] != m[1] and m[1] != m[2] and (K == 3 or m[2] != m[3])]
                sc.append(filt if filt else [m for m in c if m not in blocked])
            if any(not x for x in sc): return None, set(range(len(sel)))
            ch, unc = greedy_elems(sk, sc, frozenset())
            if unc: return None, unc
            acc |= set(ch)
        return sorted(acc), set()
    for it in range(20):
        dd = collections.Counter()
        for cs in covers.values():
            for m in cs: dd[m] += 1
        badW = [W for W in covers if (not covers[W]) or any(dd[m] > perm_count(m) for m in covers[W])]
        if not badW:
            log("阶段3 容量校验通过 (迭代 %d)" % it); break
        fixed = 0; evicted = 0
        for W in badW:
            if W not in covers: continue
            keys, cands, modes = INFO[W]
            for m in covers[W]: dd[m] -= 1
            blocked = frozenset(m for m, u in dd.items() if u >= perm_count(m))
            new, unc = cover_with(W, blocked)
            if new is None and unc:
                for j in sorted(unc):
                    if j >= len(cands): continue
                    got = False
                    for m in sorted(cands[j], key=lambda x: (dd.get(x, 0), x))[:40]:
                        for W2 in [x for x in covers if x != W and m in covers[x]][:6]:
                            for x in covers[W2]: dd[x] -= 1
                            blk2 = frozenset(x for x, u in dd.items() if u >= perm_count(x))
                            new2, unc2 = cover_with(W2, blk2)
                            if new2 is not None:
                                covers[W2] = new2
                                for x in new2: dd[x] += 1
                                got = True; evicted += 1; break
                            for x in covers[W2]: dd[x] += 1
                        if got: break
                    if got:
                        blocked = frozenset(m for m, u in dd.items() if u >= perm_count(m))
                        new, unc = cover_with(W, blocked)
                        if new is not None: break
            if new is None:
                new, _ = cover_with(W, frozenset())
                if new is None: new = sorted(covers[W])
            covers[W] = new
            for m in new: dd[m] += 1
            fixed += 1
        log("  阶段3 迭代 %d: 待修复 %d 类, 重排 %d 类, 驱逐 %d 次, Σ|S_C| = %d" % (it, len(badW), fixed, evicted, sum(len(v) for v in covers.values())))
    plan = {}
    for W, cs in covers.items():
        plan[W] = {"codes": cs, "modes": INFO[W][2], "reserved": reserved_of(W), "nelems": len(INFO[W][0])}
    dd = collections.Counter()
    for cs in plan.values():
        for m in cs["codes"]: dd[m] += 1
    bad = [m for m, c in dd.items() if c > perm_count(m)]
    log("最终: 成功 %d 类, 失败 %d ; Σ|S_C| = %d ; 不同多重集 %d ; 超容量 %d" % (
        len(plan), len(fails), sum(len(v["codes"]) for v in plan.values()), len(dd), len(bad)))
    if bad: log("超容量样例: %s" % [(m, dd[m], perm_count(m)) for m in bad[:8]])
    if fails: log("失败样例: %s" % fails[:8])
    return T, plan, fails

def make_tables():
    T, plan, fails = build_plan()
    mult_use = {}; dec = {}; plan_out = []
    perm_fail = 0; empty = 0
    for W, info in plan.items():
        seq = []
        for m in info["codes"]:
            i = mult_use.get(m, 0); mult_use[m] = i+1
            ps = sorted(set(itertools.permutations(m)))
            if i >= len(ps):
                perm_fail += 1; continue
            oc = ps[i]
            dec[oc] = tuple(sorted(W)); seq.append(list(oc))
        if not seq: empty += 1
        plan_out.append({"W": sorted(W), "codes": seq, "modes": info["modes"],
                         "reserved": [list(m) for m in info["reserved"]]})
    log("排列耗尽 %d 次 ; 无码类 %d" % (perm_fail, empty))
    json.dump({"k": K, "n_classes": len(plan), "n_codes": len(dec), "plan": plan_out,
               "fails": fails[:50]}, open(os.path.join(OUT, "plan_k%d.json" % K), "w", encoding="utf-8"), ensure_ascii=False)
    with open(os.path.join(OUT, "decode_k%d.tsv" % K), "w", encoding="utf-8") as f:
        for oc, W in sorted(dec.items()):
            f.write(" ".join(map(str, oc)) + "\t" + ",".join(map(str, W)) + "\n")
    if K == 3:
        json.dump({"k": K, "n_classes": len(plan), "n_codes": len(dec), "plan": plan_out,
                   "fails": fails[:50]}, open(os.path.join(OUT, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False)
    log("写出 plan_k%d.json / decode_k%d.tsv ; 有序码 %d / 预算 %d" % (K, K, len(dec), 34**K))
    return T, plan, dec

class Strategy:
    def __init__(self, T, plan, dec):
        self.dec = dec
        self.codes = {W: [tuple(c) for c in v["codes"]] for W, v in plan.items()}
    def decode(self, oc): return self.dec.get(tuple(oc))
    def encode(self, H):
        c = tuple(H) if len(H) == 34 else counts(H)
        W = waits13(c)
        if not W: return None
        for oc in self.codes.get(frozenset(W), []):
            need = {}
            for x in oc: need[x] = need.get(x, 0)+1
            if all(c[x] >= v for x, v in need.items()):
                rest = list(c)
                for x in oc: rest[x] -= 1
                return list(oc) + [t for t, n in enumerate(rest) for _ in range(n)]
        return None

if __name__ == "__main__":
    make_tables()
