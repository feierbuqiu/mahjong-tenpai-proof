
import sys, time, pickle, collections
sys.path.insert(0, r"D:\DSH\MJ2\work\strategy")
t0=time.time()
import table_lib as TL
T=TL.build()
print("build time %.1fs"%(time.time()-t0))
print("keys:", list(T.keys()))
CLS=T["cls"]
print("classes:", len(CLS))
for W,blocks in list(CLS.items())[:1]:
    print("sample W:", sorted(W)[:6], "blocks:", len(blocks))
    for b in blocks[:5]: print("   ", str(b)[:200])
# check PROFII_D availability
print("PROFI_D:", len(T["PROFI_D"]), "PROFII_D:", len(T["PROFII_D"]))
k=list(T["PROFII_D"].keys())[0]
am,xs=T["PROFII_D"][k]
print("sample PROFII_D:", k, "n_xs:", len(xs), "min:", str(am)[:80])
pickle.dump({"cls":T["cls"],"PROFI_D":T["PROFI_D"],"PROFII_D":T["PROFII_D"]}, open(r"D:\DSH\MJ2\work\recon\table_perA.pkl","wb"))
print("saved work/recon/table_perA.pkl")
