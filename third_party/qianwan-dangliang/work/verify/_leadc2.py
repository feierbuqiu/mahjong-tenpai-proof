
import json,hashlib,os,collections
p="work/recon/plan_k4_leadC.json"
b=open(p,"rb").read()
print("sha256:",hashlib.sha256(b).hexdigest())
print("mtime:",os.path.getmtime(p), "size:",len(b))
P=json.loads(b.decode("utf-8"))
rows=P["plan"]
print("rows:",len(rows),"sum codes:",sum(len(r["codes"]) for r in rows),"meta n_codes:",P.get("n_codes"))
allc=[tuple(c) for r in rows for c in r["codes"]]
print("distinct ordered:",len(set(allc)))
# 每类码数分布
print("classes with 0 codes:",sum(1 for r in rows if not r["codes"]))
# 长度/上限
bad=[c for c in allc if len(c)!=4 or max(collections.Counter(c).values())>4]
print("invalid codes:",len(bad))
