import time, random, itertools
exec(open(r"D:\DSH\MJ2\work\data\_tau_validate.py", encoding="utf-8").read().split("rng = random.Random(7)")[0])
rng = random.Random(7)
t0=time.time()
for trial in range(20):
    ne = rng.randint(1, 12); m = rng.randint(1, 9)
    full = (1 << ne) - 1
    sets = []
    for _ in range(m):
        v = 0
        for e in range(ne):
            if rng.random() < 0.4: v |= 1 << e
        sets.append(v | (1 << rng.randrange(ne)))
    hc = [[] for _ in range(ne)]
    for i, v in enumerate(sets):
        for e in range(ne):
            if (v >> e) & 1: hc[e].append(i)
    ta=time.time(); r = exact(sets, hc, full); tb=time.time()
    e = brute(sets, full)
    print("trial",trial,"ne",ne,"m",m,"got",len(r),"brute",e,"exact_t=%.3fs"%(tb-ta), flush=True)
    if tb-ta > 1: print("   SLOW sets:",sets, flush=True)
print("total %.1fs"%(time.time()-t0))
