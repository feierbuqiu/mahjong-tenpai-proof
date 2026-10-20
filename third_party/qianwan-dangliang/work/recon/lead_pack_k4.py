# -*- coding: utf-8 -*-
"""lead_pack_k4.py -- Lead 的 k=4 显式构造（稀缺单元优先 + 容量感知贪心）
输出 work/recon/plan_k4_lead.json, work/recon/k4_lead_report.json

覆盖单元（充分条件：码 c ⊆ 活性部 X ⇒ c ⊆ 手牌 X⊎F）：
  kind I  : 每个 X（|X|>=4）；|X|=1（单骑）用面子族 (z,M0,M1,M2)
  kind II : |am|>=4 整块一条码 ⊆ am；否则较大一侧侧覆盖；两侧皆 2 时按对展开
  kokushi : 每个国士手牌本体（12 个 + 13 面）
  chiitoi : 族 {(z,a,a,b)}，P = 33 张非 z 牌的 5 组(7,7,7,6,6) 组内对（93 对，α=5<6）
全局：① 稀缺单元(|X|<=7)按 |X| 升序全局优先分配；② 其余逐类贪心（种子=最小 |X|）。
所有分配都遵守 p4(μ)=24/∏mult! 容量 ⇒ 有序码全局不冲突。
"""
import sys, os, json, collections, time, math, itertools, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'strategy'))
import table_lib
from table_lib import CAT_BASE, MELDS_IN_CAT

HONN = ["E", "S", "W", "N", "Haku", "Hatsu", "Chun"]
def nm(t): return ("%d%s" % (t % 9 + 1, "mps"[t // 9])) if t < 27 else HONN[t - 27]
def lift(c, X):
    v = [0] * 34
    for i, x in enumerate(X): v[CAT_BASE[c] + i] = x
    return v
FACT = [math.factorial(i) for i in range(5)]
def perm_count(mu):
    c = collections.Counter(mu)
    return 24 // math.prod(FACT[v] for v in c.values())
def vec4(mu):
    v = [0] * 34
    for t in mu: v[t] += 1
    return v
def subs_k(V):
    tiles = []
    for t, c in enumerate(V):
        for _ in range(min(c, 4)): tiles.append(t)
    out = set(); n = len(tiles)
    for a in range(n):
        for b in range(a, n):
            for c in range(b, n):
                for d in range(c, n):
                    out.add((tiles[a], tiles[b], tiles[c], tiles[d]))
    return out

print("building table ...", flush=True); t0 = time.time()
T = table_lib.build(); CLS = T['cls']
print("table %.1fs, %d classes" % (time.time() - t0, len(CLS)), flush=True)
G = json.load(open(os.path.join(HERE, '..', 'data', 'out', 'global.json'), encoding='utf-8'))
def ti(s): return 27 + HONN.index(s) if s in HONN else "mps".index(s[-1]) * 9 + int(s[0]) - 1
chiit = {int(m): sorted(set(ti(d['z']) for d in lst)) for m, lst in G['chiitoi_descriptors'].items()}

print("building units ...", flush=True); t0 = time.time()
percls = {}; tanki = collections.defaultdict(set)
for W, blocks in CLS.items():
    reqs = set()
    for b in blocks:
        if b[0] == 'I':
            c = b[1][0]; inert = tuple(x for x in range(4) if x != c)
            for (cc, X) in table_lib.block_sources(T, b)[1]:
                V = lift(cc, X)
                if sum(V) >= 4: reqs.add(tuple(V))
                else: tanki[W].add((next(t for t, x in enumerate(V) if x), inert))
        elif b[0] == 'II':
            am = b[5]; s1 = b[1][1]; s2 = b[2][1]
            if sum(am) >= 4: reqs.add(tuple(am))
            elif max(s1, s2) >= 4:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    reqs.add(tuple(lift(c1, X1) if s1 >= s2 else lift(c2, X2)))
            else:
                for (c1, X1, c2, X2) in table_lib.block_sources(T, b)[1]:
                    V1 = lift(c1, X1); V2 = lift(c2, X2)
                    reqs.add(tuple(V1[i] + V2[i] for i in range(34)))
        else:
            reqs.add(tuple(b[1]))
    percls[W] = list(reqs)
print("units %.1fs total %d tanki %d" % (time.time() - t0, sum(len(v) for v in percls.values()), len(tanki)), flush=True)

usage = collections.Counter(); cover = {}
def take(mu):
    if usage[mu] < perm_count(mu):
        usage[mu] += 1; return True
    return False

# --- chiitoi / tanki 族（先占） ---
chiit_codes = collections.defaultdict(list); chiit_missing = []
z_users = collections.defaultdict(list)
for mask, zs in chiit.items():
    for z in zs: z_users[z].append(mask)
for z in sorted(z_users):
    tiles = [t for t in range(34) if t != z]
    groups = [tiles[0:7], tiles[7:14], tiles[14:21], tiles[21:27], tiles[27:33]]
    fam = [tuple(sorted((z, a, a, b))) for g in groups for a, b in itertools.combinations(g, 2)]
    for mask in z_users[z]:
        got = [mu for mu in fam if take(mu)]
        chiit_codes[mask].extend(got)
        if len(got) != len(fam): chiit_missing.append((mask, nm(z), len(fam) - len(got)))
tanki_codes = collections.defaultdict(set); tanki_missing = 0
for W, zs in tanki.items():
    for (z, inert) in zs:
        fam = set()
        for cat in inert:
            for M in MELDS_IN_CAT[cat]:
                tal = [t for t, x in enumerate(M) for _ in range(x)]
                fam.add(tuple(sorted((z, tal[0], tal[1], tal[2]))))
        for mu in fam:
            if take(mu): tanki_codes[W].add(mu)
        tanki_missing += len(fam) - len(tanki_codes[W] & fam)
print("chiitoi %d families (incomplete %d); tanki %d classes (missing %d)" % (
    sum(len(v) for v in z_users.values()), len(chiit_missing), len(tanki_codes), tanki_missing), flush=True)

# --- numpy 表示 ---
U = {W: (np.array(keys, dtype=np.int8) if keys else np.zeros((0, 34), np.int8)) for W, keys in percls.items()}
cov = {W: np.zeros(len(percls[W]), bool) for W in percls}
for W in percls: cover.setdefault(W, [])
picked = {}   # W -> set of codes already used by this class

def pick_code(W, unit_i, rng, max_cand=400, sample=True):
    """在单元 unit_i 的码中挑一个（容量允许）覆盖该类未覆盖单元最多的码"""
    keys = percls[W]; X = keys[unit_i]
    cands = list(subs_k(X))
    if sample and len(cands) > max_cand:
        rng.shuffle(cands); cands = cands[:max_cand]
    pk = picked.setdefault(W, set())
    cands = [c for c in cands if c not in pk and usage[c] < perm_count(c)]
    if not cands: return None
    rem = np.nonzero(~cov[W])[0]
    C = np.array([vec4(c) for c in cands], dtype=np.int8)
    cnt = np.zeros(len(cands), dtype=np.int32)
    sub = U[W][rem]
    for st in range(0, len(cands), 24):
        blk = C[st:st+24]
        cnt[st:st+len(blk)] = (sub[:, None, :] >= blk[None, :, :]).all(-1).sum(0)
    j = int(cnt.argmax())
    return cands[j]

def apply_code(W, c):
    picked.setdefault(W, set()).add(c); take(c); cover[W].append(c)
    cov[W] |= (U[W] >= np.array(vec4(c), dtype=np.int8)).all(-1)

rng = random.Random(20260916)
t0 = time.time(); fails = []

# --- 阶段 A：稀缺单元（|X| <= 7）全局优先 ---
scarce = []
for W, keys in percls.items():
    for i, X in enumerate(keys):
        s = sum(X)
        if s <= 7: scarce.append((s, W, i))
scarce.sort(key=lambda z: z[0])
print("phase A: %d scarce units" % len(scarce), flush=True)
nA = 0
for (s, W, i) in scarce:
    if cov[W][i]: continue
    c = pick_code(W, i, rng)
    if c is None:
        fails.append(([nm(t) for t in sorted(W)], "scarce", s, len(percls[W])))
        continue
    apply_code(W, c); nA += 1
print("phase A done %.0fs: codes=%d fails=%d" % (time.time() - t0, sum(len(v) for v in cover.values()), len(fails)), flush=True)

# --- 阶段 B：逐类贪心（种子=最小 |X|） ---
order = sorted(percls.keys(), key=lambda W: len(percls[W]))
for n_, W in enumerate(order):
    keys = percls[W]
    if not keys: continue
    sizes = np.array([sum(v) for v in keys])
    while not cov[W].all():
        rem = np.nonzero(~cov[W])[0]
        i = int(rem[np.argmin(sizes[rem])])
        c = None
        for tries in range(6):
            ii = i if tries == 0 else int(rem[rng.randrange(rem.size)])
            if cov[W][ii]: continue
            c = pick_code(W, ii, rng)
            if c is not None: break
        if c is None:
            fails.append(([nm(t) for t in sorted(W)], "greedy", int(sizes[i]), len(keys)))
            cov[W][i] = True
            continue
        apply_code(W, c)
    if n_ % 250 == 0:
        print("  B %d/%d %.0fs codes=%d fails=%d" % (n_, len(order), time.time() - t0, sum(len(v) for v in cover.values()), len(fails)), flush=True)
print("greedy %.1fs; codes %d; failures %d" % (time.time() - t0, sum(len(v) for v in cover.values()), len(fails)), flush=True)
for f in fails[:15]: print("  FAIL", f, flush=True)

# --- 输出 ---
used_perm = collections.Counter(); plan = []
for W in cover:
    codes = []
    for mu in cover[W]:
        ps = sorted(set(itertools.permutations(mu)))
        i = used_perm[mu]; assert i < len(ps), (mu, i)
        used_perm[mu] += 1; codes.append(list(ps[i]))
    codes += [list(mu) for mu in sorted(tanki_codes.get(W, ()))]
    plan.append({"W": [nm(t) for t in sorted(W)], "codes": codes})
allc = [tuple(c) for r in plan for c in r["codes"]]
rep = {"k": 4, "n_classes": len(plan), "n_codes": len(allc), "distinct_codes": len(set(allc)),
       "empty_classes": sum(1 for r in plan if not r["codes"]), "fail_units": len(fails),
       "fails": fails[:80], "chiit_missing": chiit_missing[:20], "tanki_missing": tanki_missing}
json.dump({"k": 4, "n_classes": len(plan), "n_codes": len(allc), "plan": plan}, open(os.path.join(HERE, 'plan_k4_lead.json'), 'w'))
json.dump(rep, open(os.path.join(HERE, 'k4_lead_report.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in rep.items() if k != 'fails'}, ensure_ascii=False), flush=True)
