import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "work/lowerbound"); sys.path.insert(0, "work/verify"); sys.path.insert(0, "work/strategy")
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def mk(tiles):
    H=[0]*34
    for x in tiles: H[HON[x] if x in HON else "mps".index(x[-1])*9+int(x[0])-1] += 1
    return H
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HONN[t-27]
H = mk(["4p","5p","6p","7p","8p","9p","W","N","Haku","Haku","Haku","Hatsu","Hatsu"])
print("hand:", [nm(t) for t in range(34) for _ in range(H[t])], "sum", sum(H), "max", max(H))
from lower import waits as mywaits, is_std_win, is_chiitoi_win, is_kokushi_win
print("我的 waits   :", [nm(t) for t in mywaits(tuple(H))])
for t in range(34):
    if H[t]>=4: continue
    c=list(H); c[t]+=1
    if is_std_win(c): print("   is_std_win True for +%s" % nm(t))
try:
    from indep_core import closed_form_W
    print("indep_core  :", [nm(t) for t in closed_form_W(H)])
except Exception as e: print("indep_core err", e)
try:
    from mjlib import waits13
    print("mjlib waits13:", [nm(t) for t in waits13(tuple(H))])
except Exception as e: print("mjlib err", e)
