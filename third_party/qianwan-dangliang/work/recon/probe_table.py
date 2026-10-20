
import pickle, sys, collections
sys.path.insert(0, r"D:\DSH\MJ2\work\strategy")
T=pickle.load(open(r"D:\DSH\MJ2\work\strategy\table.pkl","rb"))
print("type:", type(T))
if isinstance(T, dict):
    print("keys:", list(T.keys())[:20])
    for k,v in list(T.items())[:8]:
        print("  ",k, type(v), (len(v) if hasattr(v,'__len__') else ''))
