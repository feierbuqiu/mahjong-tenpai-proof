
import pickle, collections
T=pickle.load(open(r"D:\DSH\MJ2\work\strategy\out\table.pkl","rb"))
print("type:",type(T))
if isinstance(T,dict):
    print("keys:",list(T.keys()))
    for k,v in T.items():
        s=type(v).__name__
        n=len(v) if hasattr(v,'__len__') else ''
        print("   ",k,s,n)
        if k=="cls":
            items=list(v.items())[:1]
            for W,blocks in items:
                print("      sample class W=",sorted(W)[:6]," n_blocks=",len(blocks))
                print("      block sample:", blocks[0])
