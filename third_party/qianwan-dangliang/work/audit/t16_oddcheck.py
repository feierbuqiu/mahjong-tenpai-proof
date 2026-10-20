import sys, itertools
sys.path.insert(0,'D:/DSH/MJ2/work/audit')
from mjcore import *
# can a meld-decomposable filler F with counts<=2 and size m have exactly ONE odd count?
for L,hon in ((9,False),(7,True)):
    runs=[]
    if not hon:
        for st in range(L-2): runs.append(tuple(range(st,st+3)))
    units=runs+[ (i,) for i in range(L) ]  # triplets (count 3) allowed but counts<=2 excludes them
    for m in (3,6,9,12):
        cnt={"one_odd":0,"zero_odd":0,"other":0}
        for combo in itertools.combinations_with_replacement(runs, m//3):
            c=[0]*L
            for r in combo:
                for t in r: c[t]+=1
            if max(c)>2: continue
            odd=sum(1 for x in c if x%2)
            if odd==1: cnt["one_odd"]+=1
            elif odd==0: cnt["zero_odd"]+=1
            else: cnt["other"]+=1
        print("L=%d honors=%s m=%d -> %s" % (L,hon,m,cnt))
