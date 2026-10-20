import sys, pickle
sys.path.insert(0, r'D:\DSH\MJ2\work\strategy'); sys.path.insert(0, r'D:\DSH\MJ2\work\strategy\out')
import table_lib as TL
C = pickle.load(open(r'D:\DSH\MJ2\work\strategy\out\table_cache.pkl','rb'))
PII = C['PROFII_D']
for (c,s,k) in list(PII.keys()):
    if (c,s) == (0,2):
        am, xs = PII[(c,s,k)]
        mn = [0]*34
        for i in range(TL.CAT_LEN[c]):
            mn[TL.CAT_BASE[c]+i] = min(X[i] for X in xs)
        print("key", k, "xs", xs)
        print("  am      ", list(am))
        print("  my min  ", mn)
        break
