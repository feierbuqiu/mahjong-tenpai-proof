import sys, os, json, collections, itertools
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "work/lowerbound")
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def to_idx(w):
    o=[]
    for x in w:
        if isinstance(x,int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9+int(x[0])-1)
    return o
G = json.load(open("work/data/out/global.json", encoding="utf-8"))
Wtarget = frozenset(range(9))
rows = [r for r in G["classes"] if frozenset(to_idx(r["W"])) == Wtarget]
print("类 W={1m..9m} 的 source 数:", len(rows[0]["sources"]) if rows else 0)
if rows:
    kinds = collections.Counter(s["kind"] for s in rows[0]["sources"])
    print("   kinds:", kinds)
    for s in rows[0]["sources"]:
        if s["kind"] == "I":
            A = s["A"]; print("   I: cat=%s A=%s inert=%s sumA=%d" % (s["cat"], A, s["inert"], sum(int(c) for c in A)))
            if sum(int(c) for c in A) == 10: break
    # 检查 code (E,E,E,1m) 是否可嵌入
    c = (0, 27,27,27)
    print("  目标码:", [HONN[t-27] if t>=27 else "%d%s"%(t%9+1,"mps"[t//9]) for t in c])
    for s in rows[0]["sources"]:
        if s["kind"] != "I": continue
        ci = "mpsz".index(s["cat"]); A = [0]*34
        for i,ch in enumerate(s["A"]):
            if ch != "0": A[(0,9,18,27)[ci]+i] = int(ch)
        j = (13-sum(A))//3
        inert = ["mpsz".index(x) for x in s["inert"]]
        CAT_OF = [0]*9+[1]*9+[2]*9+[3]*7
        okA = all(A[t] >= k for t,k in collections.Counter(c).items() if CAT_OF[t]==ci)
        print("     A(size %d, j=%d) 含码在同门部分? %s" % (sum(A), j, okA))
