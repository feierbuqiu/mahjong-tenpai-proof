
exec(open(r"D:\DSH\MJ2\work\recon\recon_global2.py").read().split("# per-category signatures")[0])
# replicate Type I loop with counters, category by category
CLASS=set()
cnt_base={}; cnt_add={}
for c in range(4):
    S=[x for x in range(4) if x!=c]
    b0=len(CLASS)
    nb=0; na=0
    for size in (1,4,7,10,13):
        for X in gen(size,ncat(c)):
            Wp=0
            for t in range(ncat(c)):
                if X[t]<4:
                    l=list(X); l[t]+=1
                    if melds_pair(l): Wp |= 1<<t
            odd=[i for i,v in enumerate(X) if v%2==1]
            oddn = 1 if len(odd)==1 else (0 if not odd else 2)
            m=13-size; j=m//3
            hz,o1,_=filler_data(S,j)
            base=set(gidx(c,i) for i in range(ncat(c)) if (Wp>>i)&1)
            if Wp: CLASS.add(frozenset(base)); nb+=1
            if oddn==1 and hz and Wp: CLASS.add(frozenset(base|{gidx(c,odd[0])})); na+=1
            elif oddn==1 and hz and not Wp: CLASS.add(frozenset({gidx(c,odd[0])})); na+=1
            if oddn==0:
                for z in o1: CLASS.add(frozenset(base|{z})); na+=1
    print("cat",c,"base_adds",nb,"chiitoi_adds",na,"new classes added",len(CLASS)-b0, "cum", len(CLASS), flush=True)
print("Type I total classes:", len(CLASS), flush=True)
