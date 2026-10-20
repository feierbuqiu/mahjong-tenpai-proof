# -*- coding: utf-8 -*-
"""k3_alloc.py -- k=3 容量感知分配器 (b-匹配 + 驱逐-重覆盖).

思路:
  0) 固定 34 个单元素类 {z} 的 tanki/chiitoi 族码 (z 标记, 跨 z 天然不冲突);
  1) 逐子宇宙 U (m/p/s/z): 对"全部落在 U 内"的来源元素求核心 core=逐牌最小;
     |core|>=3 的类 -> 候选码 = ksubs(core), 用 Kuhn b-匹配(容量 p(mu))分配 1 条;
  2) 其余元素(含混合门) -> 带容量阻塞的贪心覆盖 (优先"三张不同牌", 其次未用多重集);
  3) 超容量/空类 -> 驱逐: 让某占用者改码以腾出容量, 再重覆盖.
输出 out/plan_k3.json / out/decode_k3.tsv
"""
import sys, os, json, time, itertools, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
import strategy as SG
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
K = 3
T0 = time.time()
def log(*a): print("[%7.1fs]" % (time.time()-T0), *a, flush=True)
SG.K = K
pc = SG.perm_count
ksubs = SG.ksubs

T = TL.build(); CLS = T["cls"]
INFO = {}
for W, blocks in CLS.items():
    INFO[W] = SG.class_elements(T, W, blocks)
log("类数 %d, Σ元素 %d" % (len(CLS), sum(len(v[0]) for v in INFO.values())))

def support(key):
    v = key[2] if key[0] == "S" else key[1]
    return {cat_of(i) for i, n in enumerate(v) if n}
def vec(key):
    return key[2] if key[0] == "S" else key[1]

# ---------- 0) 单元素类固定族码 ----------
covers = {}
usage = collections.Counter()
for W in CLS:
    if len(W) == 1:
        z = next(iter(W))
        S = tuple(x for x in range(4) if x != cat_of(z))
        fam = sorted(SG.tanki_patterns(z, S) | SG.chiitoi_patterns(z))
        covers[W] = fam
        for m in fam: usage[m] += 1
log("阶段0 单元素类固定: %d 类, %d 码" % (sum(1 for W in CLS if len(W)==1), sum(len(covers[W]) for W in covers)))
log("  空 elements 的类: %d ; 阶段0 后空码类: %d" % (sum(1 for W in INFO if not INFO[W][0]), sum(1 for W in CLS if not covers.get(W))))

# ---------- 1) 子宇宙: 核心码 + Kuhn b-匹配 ----------
matched = {}
def run_universe(U):
    classes = []
    for W, (keys, cands, modes) in INFO.items():
        if W in covers and len(covers[W]) > 0 and len(W) == 1: continue
        els = [k for k in keys if support(k) == {U}]
        if not els: continue
        core = [min(vec(k)[i] for k in els) for i in range(34)]
        classes.append((W, els, core, sum(core)))
    CAND = {}
    free = []
    for W, els, core, su in classes:
        if su >= K: CAND[W] = sorted(ksubs(tuple(core)))
        else: free.append(W)
    # Kuhn
    match = collections.defaultdict(list)
    def try_assign(W, visited):
        for m in CAND[W]:
            if m in visited: continue
            visited.add(m)
            occ = match[m]
            if len(occ) < pc(m):
                occ.append(W); return True
            for W2 in list(occ):
                if try_assign(W2, visited):
                    occ.remove(W2); occ.append(W); return True
        return False
    done = 0
    for W in sorted(CAND, key=lambda x: len(CAND[x])):
        if try_assign(W, set()): done += 1
    inv = {}
    for m, occ in match.items():
        for W in occ: inv[W] = m
        usage[m] += len(occ)
    log("  宇宙 %s: 类 %d (核心码 %d, 多码 %d) -> 匹配成功 %d" % (U, len(classes), len(CAND), len(free), done))
    return inv, free, {W: CAND.get(W) for W in CAND}

def vec_cat(c, X):
    return SG.vec_of(c, X)

# ---------- 2) 多码类 + 混合元素: 带容量阻塞的贪心 ----------
def cover_class(W, only_stage=None, allow_all=True):
    """返回 (codes, uncovered_count)"""
    keys, cands, modes = INFO[W]
    acc = set(covers.get(W, []))
    unc_all = 0
    for stage in (0, 1):
        if only_stage is not None and stage != only_stage: continue
        sel = [i for i, k in enumerate(keys) if (len(support(k)) <= 1) == (stage == 0)]
        if not sel: continue
        sk = [keys[i] for i in sel]
        sc = []
        for i in sel:
            c = cands[i]
            d = [m for m in c if m[0] != m[1] and m[1] != m[2]]
            sc.append(d if d else list(c))
        blocked = frozenset(m for m, u in usage.items() if u >= pc(m))
        ch, unc = SG.greedy_elems(sk, sc, blocked)
        if unc:
            for j in sorted(unc):
                if not sc[j]: continue
                avail = [m for m in sc[j] if usage.get(m, 0) < pc(m)]
                pool = avail if avail else sc[j]
                ch.append(min(pool, key=lambda m: (usage.get(m, 0), m)))
        acc |= set(ch)
    return sorted(acc)

# 子宇宙里"无核心码"的类: 先覆盖单门元素
ALLW = sorted(CLS.keys(), key=lambda W: (0 if len({c for k in INFO[W][0] for c in support(k)}) <= 1 else 1, len(INFO[W][0])))
univ = {}
for U in range(4):
    univ[U] = [k for k in INFO]
# 逐子宇宙处理
for U in (0, 1, 2, 3):
    classes = []
    for W, (keys, cands, modes) in INFO.items():
        els = [k for k in keys if support(k) == {U}]
        if not els: continue
        classes.append((W, els))
    _DBG = frozenset([1, 4, 20, 23, 26])
    if any(W == _DBG for W, _ in classes):
        log("  DBG U=%d: 目标类在 classes 中, els=%d" % (U, len([e for w, e in classes if w == _DBG][0])))
    for W, els in sorted(classes, key=lambda x: len(x[1])):
        if W in covers and len(covers[W]) > 0 and len(W) == 1: continue
        core = [min(vec(k)[i] for k in els) for i in range(34)]
        if sum(core) >= K:
            cands_core = sorted(ksubs(tuple(core)))
            avail = [m for m in cands_core if usage.get(m, 0) < pc(m)]
            if avail:
                m0 = min(avail, key=lambda m: (usage.get(m, 0), m))
                covers[W] = sorted(set(covers.get(W, [])) | {m0}); usage[m0] += 1
                continue
        # 多码: 贪心覆盖这些元素(带阻塞)
        els_v = [vec(k) for k in els]
        cand = []
        for v in els_v:
            d = [m for m in ksubs(v) if m[0] != m[1] and m[1] != m[2] and usage.get(m, 0) < pc(m)]
            cand.append(d if d else [m for m in ksubs(v) if usage.get(m, 0) < pc(m)])
        ch, unc = SG.greedy_elems(els_v, cand, frozenset())
        if unc:
            for j in sorted(unc):
                if not cand[j]: continue
                ch.append(min(cand[j], key=lambda m: (usage.get(m, 0), m)))
        covers[W] = sorted(set(covers.get(W, [])) | set(ch))
        for m in set(ch): usage[m] += 1
        if W == _DBG: log("  DBG U=%d 目标类被赋码: %s" % (U, covers[W]))
log("子宇宙单门元素覆盖完成: Σ|S_C| = %d, 不同多重集 %d, 空码类 %d" % (sum(len(v) for v in covers.values()), len(usage), sum(1 for W in CLS if not covers.get(W))))

# ---------- 混合元素 ----------
for W in ALLW:
    keys, cands, modes = INFO[W]
    sel = [i for i, k in enumerate(keys) if len(support(k)) > 1]
    if not sel: continue
    sk = [keys[i] for i in sel]
    sc = []
    for i in sel:
        c = cands[i]
        d = [m for m in c if m[0] != m[1] and m[1] != m[2]]
        sc.append(d if d else list(c))
    blocked = frozenset(m for m, u in usage.items() if u >= pc(m))
    ch, unc = SG.greedy_elems(sk, sc, blocked)
    if unc:
        for j in sorted(unc):
            if not sc[j]: continue
            avail = [m for m in sc[j] if usage.get(m, 0) < pc(m)]
            pool = avail if avail else sc[j]
            ch.append(min(pool, key=lambda m: (usage.get(m, 0), m)))
    covers[W] = sorted(set(covers.get(W, [])) | set(ch))
    for m in set(ch): usage[m] += 1
log("混合元素覆盖完成: Σ|S_C| = %d, 不同多重集 %d, 空码类 %d" % (sum(len(v) for v in covers.values()), len(usage), sum(1 for W in CLS if not covers.get(W))))

# ---------- 3) 容量修复(精确按真实覆盖) ----------
def cover_full(W, blocked):
    keys, cands, modes = INFO[W]
    acc = set(SG.tanki_patterns(next(iter(W)), tuple(x for x in range(4) if x != cat_of(next(iter(W))))) | SG.chiitoi_patterns(next(iter(W)))) if len(W) == 1 else set()
    for stage in (0, 1):
        sel = [i for i, k in enumerate(keys) if (len(support(k)) <= 1) == (stage == 0)]
        if not sel: continue
        sk = [keys[i] for i in sel]; sc = []
        for i in sel:
            c = cands[i]
            d = [m for m in c if m not in blocked and m[0] != m[1] and m[1] != m[2]]
            sc.append(d if d else [m for m in c if m not in blocked])
        if any(not x for x in sc): return None
        ch, unc = SG.greedy_elems(sk, sc, frozenset())
        if unc: return None
        acc |= set(ch)
    return sorted(acc)

for it in range(8):
    dd = collections.Counter()
    for cs in covers.values():
        for m in cs: dd[m] += 1
    badW = [W for W in covers if (not covers[W]) or any(dd[m] > pc(m) for m in covers[W])]
    if not badW:
        log("容量校验通过 (迭代 %d)" % it); break
    nfix = 0
    for W in badW:
        for m in covers[W]: dd[m] -= 1
        blocked = frozenset(m for m, u in dd.items() if u >= pc(m))
        new = cover_full(W, blocked)
        if new is None:
            for m in sorted([m for m in list(covers[W])], key=lambda x: dd.get(x, 0))[:3]:
                for W2 in [x for x in covers if x != W and m in covers[x]][:4]:
                    for y in covers[W2]: dd[y] -= 1
                    b2 = frozenset(y for y, u in dd.items() if u >= pc(y))
                    n2 = cover_full(W2, b2)
                    if n2 is not None:
                        covers[W2] = n2
                        for y in n2: dd[y] += 1
                        break
                    for y in covers[W2]: dd[y] += 1
                blocked = frozenset(y for y, u in dd.items() if u >= pc(y))
                new = cover_full(W, blocked)
                if new is not None: break
        if new is None: new = sorted(covers[W])
        covers[W] = new
        for m in new: dd[m] += 1
        nfix += 1
    log("  容量修复 迭代 %d: 待修 %d, 已修 %d, Σ|S_C| = %d" % (it, len(badW), nfix, sum(len(v) for v in covers.values())))

dd = collections.Counter()
for cs in covers.values():
    for m in cs: dd[m] += 1
over = [m for m, c in dd.items() if c > pc(m)]
empty = [W for W in covers if not covers[W]]
log("最终: 类 %d, Σ|S_C| = %d, 超容量多重集 %d, 空码类 %d" % (
    len(covers), sum(len(v) for v in covers.values()), len(over), len(empty)))

# ---------- 输出 ----------
mul_use = {}; dec = {}; plan_out = []
for W, cs in covers.items():
    seq = []
    for m in cs:
        i = mul_use.get(m, 0); mul_use[m] = i+1
        ps = sorted(set(itertools.permutations(m)))
        if i >= len(ps): continue
        oc = ps[i]; dec[oc] = tuple(sorted(W)); seq.append(list(oc))
    plan_out.append({"W": sorted(W), "codes": seq})
json.dump({"k": K, "n_classes": len(plan_out), "n_codes": len(dec), "plan": plan_out,
           "over_capacity_multisets": len(over), "empty_classes": len(empty)},
          open(os.path.join(OUT, "plan_k3.json"), "w", encoding="utf-8"), ensure_ascii=False)
with open(os.path.join(OUT, "decode_k3.tsv"), "w", encoding="utf-8") as f:
    for oc, W in sorted(dec.items()):
        f.write(" ".join(map(str, oc)) + "\t" + ",".join(map(str, W)) + "\n")
log("写出 out/plan_k3.json / out/decode_k3.tsv ; 有序码 %d / 预算 %d" % (len(dec), 34**K))
