import sys, pickle, json
sys.path.insert(0,r'D:\DSH\MJ2\work\strategy'); sys.path.insert(0,r'D:\DSH\MJ2\work\strategy\out')
C=pickle.load(open(r'D:\DSH\MJ2\work\strategy\out\table_cache.pkl','rb'))
cls=C['cls']; PI=C['PROFI_D']; PII=C['PROFII_D']
# find an II block
for W,blocks in cls.items():
    for b in blocks:
        if b[0]=='II':
            print("II block:", [type(x).__name__ for x in b], len(b))
            print("  b[1] =", str(b[1])[:120])
            print("  b[2] =", str(b[2])[:120])
            print("  PII[b[1]] len e[1] =", len(PII[b[1]][1]), "sample", PII[b[1]][1][:2])
            print("  W =", sorted(W))
            break
    else: continue
    break
# unit counts
nI=0; nII=0
kinds={}
for W,blocks in cls.items():
    for b in blocks:
        if b[0]=='I':
            e=PI.get(b[1])
            if e: nI+=len(e[1])
        elif b[0]=='II':
            e1=PII.get(b[1]); e2=PII.get(b[2])
            if e1 and e2: nII+=len(e1[1])*len(e2[1])
        kinds[b[0]]=kinds.get(b[0],0)+1
print("I units:", nI, " II units:", nII, " block kinds:", kinds)
print("blocks per class: max", max(len(v) for v in cls.values()))
