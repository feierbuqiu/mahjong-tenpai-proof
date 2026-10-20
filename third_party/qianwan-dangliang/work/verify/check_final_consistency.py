
import json,hashlib
P="work/verify/plan_k4_FINAL.json"
sha=hashlib.sha256(open(P,"rb").read()).hexdigest()
cert=json.load(open("work/verify/final_certificate.json",encoding="utf-8"))
f=json.load(open(P,encoding="utf-8"))
same_path = cert["plan"]["path"]=="work/verify/plan_k4_FINAL.json"
same_sha  = cert["plan"]["sha256"]==sha
same_cnt  = cert["plan"]["n_codes"]==f["n_codes"]==17579 and cert["plan"]["n_classes"]==f["n_classes"]==2846
print("file        :",P)
print("file sha256 :",sha)
print("cert path   :",cert["plan"]["path"], "=> same:",same_path)
print("cert sha256 :",cert["plan"]["sha256"], "=> same:",same_sha)
print("codes/classes cert/file:",cert["plan"]["n_codes"],"/",cert["plan"]["n_classes"],"== file:",same_cnt)
print("plan_k4_FINAL.sha256 file:",open("work/verify/plan_k4_FINAL.sha256").read().split()[0]==sha)
print("CONSISTENT:", bool(same_path and same_sha and same_cnt))
