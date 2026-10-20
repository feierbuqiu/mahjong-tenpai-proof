"""Summarise the kernel build: per-module times from the lake log, split by check family.

usage: python -I timing.py <split.txt> <full_build.log> <Run dir>
A module's measured time is shared among its leaves in proportion to their estimated costs.
"""
import sys, re, os, collections

split_path, log_path, run_dir = sys.argv[1:4]
SMALL = {'decode_ok': 10.0, 't0_ok': 5.0, 't3_ok': 11.0, 'k_ok': 35.0, 'wit_ok': 12.0, 'wit_len': 0.1}
est = dict(SMALL)
fam = {k: 'small' for k in SMALL}

def pname(ds):
    return 'p' + ''.join(ds)

for line in open(split_path):
    a = line.split()
    if not a:
        continue
    if a[0] == 'T1':
        nm = f'T1_{a[1]}_{a[2]}_{pname(a[4:])}'; est[nm] = float(a[3]); fam[nm] = 'T1'
    elif a[0] == 'T2':
        nm = f'T2_{a[1]}_{a[2]}_{a[3]}_{a[4]}_{pname(a[7:])}'; est[nm] = float(a[6]); fam[nm] = 'T2'
    elif a[0] == 'T4A':
        nm = f'T4A_{a[1]}_{a[2]}'; est[nm] = float(a[4]); fam[nm] = 'T4'
    elif a[0] == 'T4B':
        nm = f'T4B_{a[1]}_{a[2]}_{a[3]}'; est[nm] = float(a[5]); fam[nm] = 'T4'

mod_leaves = {}
for f in os.listdir(run_dir):
    if f.startswith('K') and f.endswith('.lean'):
        names = re.findall(r'^theorem (\S+) :', open(os.path.join(run_dir, f), encoding='utf-8').read(), re.M)
        mod_leaves[f[:-5]] = names

def secs(s):
    m = re.match(r'([\d.]+)(ms|s|m|h)', s)
    v, u = float(m.group(1)), m.group(2)
    return v / 1000 if u == 'ms' else v if u == 's' else v * 60 if u == 'm' else v * 3600

mod_time = {}
other = []
for line in open(log_path, encoding='utf-8', errors='replace'):
    m = re.search(r'Built Tenpai\.(\S+) \(([\d.]+(?:ms|s|m|h))\)', line)
    if m:
        name, t = m.group(1), secs(m.group(2))
        if name.startswith('Run.K'):
            mod_time[name[4:]] = t
        else:
            other.append((name, t))

leaves_n = collections.Counter(fam[n] for ns in mod_leaves.values() for n in ns)
est_f = collections.Counter()
act_f = collections.Counter()
for mod, ns in mod_leaves.items():
    tot = sum(est[n] for n in ns)
    for n in ns:
        est_f[fam[n]] += est[n]
        act_f[fam[n]] += mod_time.get(mod, 0.0) * est[n] / tot
print(f'modules timed: {len(mod_time)} / {len(mod_leaves)}')
print(f'{"family":8} {"leaves":>7} {"est s":>9} {"measured s":>11}')
for f in ['T1', 'T2', 'T4', 'small']:
    print(f'{f:8} {leaves_n[f]:7d} {est_f[f]:9.0f} {act_f[f]:11.0f}')
print(f'{"total":8} {sum(leaves_n.values()):7d} {sum(est_f.values()):9.0f} {sum(mod_time.values()):11.0f}')
ts = sorted(mod_time.values())
print(f'module time: min {ts[0]:.0f}s  median {ts[len(ts)//2]:.0f}s  max {ts[-1]:.0f}s')
for name, t in other:
    print(f'other module {name}: {t:.1f}s')
