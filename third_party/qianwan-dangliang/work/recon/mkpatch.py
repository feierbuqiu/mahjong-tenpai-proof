
import io
path=r"D:\DSH\MJ2\work\recon\build_v18.py"
src=open(path,encoding="utf-8").read().split("\n")
# line numbers are 1-based from grep: 107..133 fallback block, 134..135 put-fail discard
fb=src[106:133]           # lines 107..133
rest=src[:106]+src[133:]  # remove fallback block
# 在 put-fail 行处插入: best=None + fallback
idx=None
for i,l in enumerate(rest):
    if "if not put(best,new):" in l: idx=i; break
new=[]
new += rest[:idx]
new.append("        if best is not None and not put(best,new):")
new.append("            best=None")
new += fb
new += ["        else:"] + ["    "+l if l.strip() else l for l in rest[idx+2:idx+3]]
# 去掉可能重复的 continue/unc 结构: 简单处理: rest[idx+1] 是 "            unc.discard(i); continue"
new += rest[idx+3:]
out="\n".join(new).replace('plan_k4_u16.json','plan_k4_u19.json')
open(r"D:\DSH\MJ2\work\recon\build_v20.py","w",encoding="utf-8").write(out)
print("patched -> build_v20.py")
