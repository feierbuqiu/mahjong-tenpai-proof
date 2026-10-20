
import numpy as np, json, collections
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def t2s(t): return ("%d%s"%((t%9)+1,"mps"[t//9])) if t<27 else HON[t-27]
def s2t(s):
    H={n:27+i for i,n in enumerate(HON)}
    if s in H: return H[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
z=np.load(r"D:\DSH\MJ2\work\verify\cache_w_p.npz")
hands=z["hands"]; wids=z["wids"]
u=collections.Counter(wids.tolist())
print("distinct wids:", len(u), " sample:", sorted(u.items())[:5])
target=(1<<11)|(1<<15)   # 3p,7p
print("target Wmask 3p,7p =", target, "present:", target in u, "count:", u.get(target))
# 也可能是重映射的 id
print("max wid:", wids.max(), "min:", wids.min())
