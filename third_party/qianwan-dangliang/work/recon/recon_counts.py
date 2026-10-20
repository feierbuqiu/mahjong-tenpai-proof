
import sys, itertools, json, time
from collections import defaultdict

# tile index: 0-8 m1-9, 9-17 p1-9, 18-26 s1-9, 27-33 honors(z1-7)
CAT = [0]*9 + [1]*9 + [2]*9 + [3]*7

def suit_melds(n=9):
    # BFS over count vectors produced by melds, max 4 melds, counts <=4
    zero = tuple([0]*n)
    layers = [ {zero: None} ]
    cur = {zero}
    for k in range(4):
        nxt = set()
        for v in cur:
            for i in range(n-2):  # run
                if v[i] < 4 and v[i+1] < 4 and v[i+2] < 4:
                    w = list(v); w[i]+=1; w[i+1]+=1; w[i+2]+=1
                    nxt.add(tuple(w))
            for i in range(n):    # triplet
                if v[i] <= 1:
                    w = list(v); w[i]+=3
                    nxt.add(tuple(w))
        layers.append(nxt)
        cur = nxt
    return layers  # layers[k] = count vectors achievable with exactly k melds

t0=time.time()
L = suit_melds(9)
H = suit_melds(7)
print("suit meld-vector counts by k:", [len(x) for x in L], flush=True)
print("honor meld-vector counts by k:", [len(x) for x in H], flush=True)

# pairs
def pairs(n):
    return [tuple(1 if i==j else 0 for i in range(n)) for j in range(n)]
SP = pairs(9); HP = pairs(7)

suit_names = ['m','p','s']
def vec_to_tiles(vec, base):
    out=[]
    for i,c in enumerate(vec):
        out += [base+i]*c
    return out

winning = set()
# choose for each of 4 categories: k melds (sum 4) and optionally pair
cats = [('s',L,SP),('s',L,SP),('s',L,SP),('h',H,HP)]
# iterate over k distribution and pair placement
for kdist in itertools.product(range(5), repeat=4):
    if sum(kdist)!=4: continue
    for paircat in range(5):  # 0..3 category index, 4 = none -> but must have pair
        pass
    for paircat in range(4):
        opts=[]
        for c in range(4):
            _,Lc,Pc = cats[c]
            opts.append(Lc[kdist[c]])
        for combo in itertools.product(*opts):
            for pv in cats[paircat][2]:
                vecs = []
                ok=True
                for c in range(4):
                    v = list(combo[c])
                    if c==paircat:
                        for i in range(len(v)):
                            v[i]+=pv[i]
                        if any(x>4 for x in v): ok=False; break
                    vecs.append(tuple(v))
                if not ok: continue
                full=[]
                for c in range(4):
                    base = c*9 if c<3 else 27
                    full += vec_to_tiles(vecs[c], base)
                if len(full)!=14: continue
                winning.add(tuple(sorted(full)))
print("distinct 4-melds+pair winning hands:", len(winning), "t=%.1fs"%(time.time()-t0), flush=True)

# chiitoitsu
chiitoi=set()
for combo in itertools.combinations(range(34),7):
    t=[]
    for c in combo: t += [c,c]
    chiitoi.add(tuple(sorted(t)))
print("chiitoitsu:", len(chiitoi), flush=True)
winning |= chiitoi

# kokushi
terminals=[0,8,9,17,18,26]+list(range(27,34))
kok=set()
for combo in itertools.combinations(terminals,13):
    for dup in combo:
        t=list(combo)+[dup]
        kok.add(tuple(sorted(t)))
print("kokushi winning hands:", len(kok), flush=True)
winning |= kok
print("total distinct winning 14-tile hands:", len(winning), flush=True)

# tenpai hands
tenpai=set()
for w in winning:
    s=set(w)
    for t in s:
        h=list(w); h.remove(t)
        tenpai.add(tuple(h))
print("distinct tenpai 13-tile hands:", len(tenpai), "t=%.1fs"%(time.time()-t0), flush=True)
json.dump({"n_winning":len(winning),"n_tenpai":len(tenpai)}, open(r"D:\DSH\MJ2\work\recon\counts.json","w"))
