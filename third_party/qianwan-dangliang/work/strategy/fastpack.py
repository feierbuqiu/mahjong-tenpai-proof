# -*- coding: utf-8 -*-
"""fastpack.py -- 加速管线: table 缓存 + numpy 向量化覆盖 + Pool(12) 按类并行.
- out/table_cache.pkl: table_lib.build() 结果 pickle(cold 首次落盘, 之后 load)
- 覆盖计数: 用 numpy 广播 (codes[:,None,:] <= units[None,:,:]).all(-1) 分块
- 并行: 每个 worker 处理一个类子集(initializer 载入 T), 只做"按类独立"的覆盖;
        全局容量/排列分配保持串行(在 main 中)
"""
import sys, os, json, time, pickle, itertools, collections, multiprocessing as mp
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import table_lib as TL
K = 4
OUT = os.path.join(HERE, "out")
CACHE = os.path.join(OUT, "table_cache.pkl")
CAP = 4

def load_table(report=None):
    t0 = time.time()
    if os.path.exists(CACHE):
        T = pickle.load(open(CACHE, "rb")); mode = "cached"
    else:
        T = TL.build(); pickle.dump(T, open(CACHE, "wb")); mode = "cold"
    dt = time.time() - t0
    if report is not None: report["table_%s_s" % mode] = dt
    return T, mode, dt

# ---------- 单元(活性向量) ----------
_T = None
def _init_worker(cache_path):
    """worker 自己从 pickle 载入 table(避免把 17MB table 经 Pool 反复 pickle)"""
    global _T, _CLS
    _T = pickle.load(open(cache_path, "rb")); _CLS = _T["cls"]

SUBCACHE = {}
def subs_of(vec):
    """4-多重集(计数向量, numpy int8) ; 按 vec 缓存"""
    r = SUBCACHE.get(vec)
    if r is not None: return r
    tiles = [t for t, n in enumerate(vec) for _ in range(min(int(n), 4))]
    out = []
    for combo in itertools.combinations_with_replacement(tiles, K):
        need = {}
        for x in combo: need[x] = need.get(x, 0) + 1
        if all(vec[x] >= v for x, v in need.items()): out.append(combo)
    arr = np.array(sorted(set(out)), dtype=np.int8) if out else np.zeros((0, K), dtype=np.int8)
    SUBCACHE[vec] = arr
    return arr

def units_of(T, W):
    reqs = set()
    for b in T["cls"][W]:
        k = b[0]
        if k == "I":
            for (cc, X) in TL.block_sources(T, b)[1]:
                v = [0]*34
                for i, x in enumerate(X): v[TL.CAT_BASE[cc]+i] = x
                if sum(v) >= K: reqs.add(tuple(v))
        elif k == "II":
            am = b[5]
            if sum(am) >= K: reqs.add(tuple(am))
            else:
                for (c1, X1, c2, X2) in TL.block_sources(T, b)[1]:
                    v = [0]*34
                    if b[1][1] >= b[2][1]:
                        for i, x in enumerate(X1): v[TL.CAT_BASE[c1]+i] = x
                    else:
                        for i, x in enumerate(X2): v[TL.CAT_BASE[c2]+i] = x
                    reqs.add(tuple(v))
        else:
            reqs.add(tuple(b[1]))
    return list(reqs)

def to_mat(vecs):
    """list of 4-元组 or 34-向量 -> np 数组"""
    if not vecs: return np.zeros((0, 34), dtype=np.int8)
    if len(vecs[0]) == 34: return np.array(vecs, dtype=np.int8)
    M = np.zeros((len(vecs), 34), dtype=np.int8)
    for i, c in enumerate(vecs):
        for t in c: M[i, t] += 1
    return M

def cover_units_np(unit_vecs, dim=34):
    """numpy 向量化贪心覆盖: 返回 (chosen_multisets, uncovered_count)"""
    U = np.array(unit_vecs, dtype=np.int16)          # n x 34
    n = U.shape[0]
    covered = np.zeros(n, dtype=bool)
    chosen = []
    while True:
        left = np.nonzero(~covered)[0]
        if left.size == 0: return chosen, 0
        cand_mats = [subs_of(tuple(U[i])) for i in left]
        # 全局候选去重
        allc = np.vstack([m for m in cand_mats if m.shape[0]]) if any(m.shape[0] for m in cand_mats) else np.zeros((0, K), np.int8)
        if allc.shape[0] == 0: return chosen, int(left.size)
        uniq = np.unique(allc, axis=0)
        C = np.zeros((uniq.shape[0], 34), dtype=np.int16)
        for j in range(uniq.shape[0]):
            for t in uniq[j]: C[j, t] += 1
        best = None; bestc = 0
        CH = 4000
        for s in range(0, C.shape[0], CH):
            blk = C[s:s+CH]
            cov = (blk[:, None, :] <= U[None, :, :]).all(-1)      # cand x unit
            cnt = cov[:, left].sum(1)
            j = int(np.argmax(cnt))
            if cnt[j] > bestc: bestc = int(cnt[j]); best = blk[j]
        if best is None or bestc == 0: return chosen, int(left.size)
        chosen.append(tuple(int(t) for t in np.repeat(np.arange(34), best)))
        hit = (best[None, :] <= U).all(-1)
        covered |= hit
        if len(chosen) > 5000: return chosen, int((~covered).sum())

def _worker_cover(Ws):
    res = {}
    for W in Ws:
        us = units_of(_T, W)
        ch, unc = cover_units_np(us)
        res[W] = (ch, unc)
    return res

def benchmark(nclass=300, seed=0, workers=12, report=None):
    T, mode, dt = load_table(report)
    keys = sorted(T["cls"].keys(), key=lambda S: sorted(S))[:nclass]
    t0 = time.time(); ser = {W: cover_units_np(units_of(T, W)) for W in keys}; t_ser = time.time()-t0
    # 按"块数"估计权重做贪心均衡分片(大类优先)
    wts = {W: len(T["cls"][W]) for W in keys}
    chunks = [[] for _ in range(workers)]
    load = [0]*workers
    for W in sorted(keys, key=lambda S: -wts[S]):
        i = load.index(min(load)); chunks[i].append(W); load[i] += wts[W]
    chunks = [c for c in chunks if c]
    t0 = time.time()
    with mp.Pool(workers, initializer=_init_worker, initargs=(CACHE,)) as pool:
        parts = pool.map(_worker_cover, chunks)
    par = {}
    for p in parts: par.update(p)
    t_par = time.time()-t0
    same = all(ser[W][0] == par[W][0] for W in keys)
    if report is not None:
        report.update({"nclass": len(keys), "table_mode": mode, "serial_s": t_ser, "parallel_s": t_par,
                       "speedup": (t_ser/t_par if t_par else None), "identical": same,
                       "sum_codes_serial": sum(len(v[0]) for v in ser.values()),
                       "sum_codes_parallel": sum(len(v[0]) for v in par.values())})
    return report, same, ser, par

if __name__ == "__main__":
    rep = {}
    b, same, ser, par = benchmark(300, report=rep)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    print("identical:", same)
    json.dump(rep, open(os.path.join(OUT, "fastpack_bench.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
