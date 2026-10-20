
exec(open(r"D:\DSH\MJ2\work\recon\recon_global2.py").read().split("# per-category signatures")[0])
c=0; n=9
cnt_x=0; cnt_add=0; added=set(); base_classes=set()
for X in gen(4,n):
    Wp=0
    for t in range(n):
        if X[t]<4:
            l=list(X); l[t]+=1
            if melds_pair(l): Wp |= 1<<t
    odd=[i for i,v in enumerate(X) if v%2==1]
    oddn = 1 if len(odd)==1 else (0 if not odd else 2)
    if oddn==0 and Wp:
        cnt_x += 1
        base=set(gidx(c,i) for i in range(n) if (Wp>>i)&1)
        hz,o1,_=filler_data([1,2,3],3)
        for z in o1:
            s=frozenset(base|{z})
            if s not in added: cnt_add+=1
            added.add(s)
        base_classes.add(frozenset(base))
print("X(size4,oddn0,Wp!=0) =", cnt_x, " distinct base classes =", len(base_classes))
print("distinct added classes =", cnt_add)
print("Wp(1122m) ex:", X)
# check odd1tiles content
hz,o1,cnt=filler_data([1,2,3],3)
print("odd1 has", len(o1), "tiles; includes 3p?", 2*9+2 in o1, " includes 1s?", 18 in o1)
