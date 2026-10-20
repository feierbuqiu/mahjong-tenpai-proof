
import hashlib,os
files=["lean/Mj/Basic.lean","lean/Mj.lean","lean/lakefile.toml","lean/Mj/Protocol.lean","lean/Mj/Disproof.lean","lean/Mj/SmokeTest.lean","lean/Mj/Lemma.lean"]
lines=[]
for f in files:
    if os.path.exists(f):
        h=hashlib.sha256(open(f,"rb").read()).hexdigest()
        lines.append("%s %s"%(f,h)); print("  %-28s %s" % (f,h[:16]))
open("work/verify/_lean_frozen_hashes.txt","w").write("\n".join(lines)+"\n")
print("snapshot refreshed")
