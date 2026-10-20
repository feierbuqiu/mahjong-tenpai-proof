import json,sys
sys.path.insert(0, r"D:\DSH\MJ2\work\data")
A=set(json.load(open(r"D:\DSH\MJ2\work\data\out\_probe_strict_classes.json"))["strict_masks"])
B=set(json.load(open(r"D:\DSH\MJ2\work\data\out\_probe_parity_masks.json"))["masks"])
U=A|B
sizes={}
for m in U: sizes[bin(m).count("1")]=sizes.get(bin(m).count("1"),0)+1
print("strict A:",len(A)," parity-B:",len(B)," new from B:",len(B-A)," union:",len(U))
print("by |W|:",dict(sorted(sizes.items())))
