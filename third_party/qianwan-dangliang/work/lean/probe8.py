import sys, pickle, collections, json
sys.path.insert(0, r'D:\DSH\MJ2\work\strategy'); sys.path.insert(0, r'D:\DSH\MJ2\work\strategy\out')
C = pickle.load(open(r'D:\DSH\MJ2\work\strategy\out\table_cache.pkl','rb'))
cls, PII = C['cls'], C['PROFII_D']
print("PROFII_D entries:", len(PII))
ks = collections.Counter((c,s) for (c,s,k) in PII)
print("per (c,s):", dict(ks))
mx = 0
for (c,s,k) in PII:
    n = len(PII[(c,s,k)][1])
    pass
# block records
nb = 0; perclass = []
for W, blocks in cls.items():
    for b in blocks:
        if b[0] == 'II': nb += 1; perclass.append(len(PII[b[1]][1])*len(PII[b[2]][1]))
print("II blocks:", nb, "units:", sum(perclass), "max pairs per block:", max(perclass))
# key sample
kk = list(PII.keys())[5]
print("sample key:", kk, "n xs:", len(PII[kk][1]), "am sum:", sum(PII[kk][0]))
# how many classes have II blocks and their index if planData order = plan JSON order
P = json.load(open(r'D:\DSH\MJ2\work\verify\plan_k4_FINAL.json', encoding='utf-8'))
HON = ["E","S","W","N","Haku","Hatsu","Chun"]; HONI = {n:27+i for i,n in enumerate(HON)}
def to_idx(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
order=[]; seen=set()
for r in P['plan']:
    W=frozenset(to_idx(x) for x in r['W'])
    if W not in seen: seen.add(W); order.append(W)
print("order len:", len(order), "== cls keys:", set(order)==set(cls))
classWithII = sum(1 for W in order if any(b[0]=='II' for b in cls[W]))
print("classes with II blocks:", classWithII)
# max profile index per (c,s)
for (c,s) in sorted(set((c,s) for (c,s,k) in PII)):
    n = sum(1 for (cc,ss,k) in PII if cc==c and ss==s)
    print("  (c=%d,s=%2d) profiles=%d" % (c,s,n), end="")
print()
