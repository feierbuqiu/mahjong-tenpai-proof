"""Generate the Lean data files of the formal proof from the plain-text plan.

usage: python -I gen_data.py <plan.txt> <u7_certificate.txt> <outdir>

* Tenpai/Data/ClassTree.lean : classTree  : PTree (List Nat)   wait mask -> encoded ordered codes
* Tenpai/Data/DecodeTree.lean: decodeTree : PTree Nat          encoded code -> wait mask
* Tenpai/Data/Cuts.lean      : cutsOf z   : List Nat           group cut points for single z (seven pairs)
* Tenpai/Data/Witness.lean   : witnesses  : List Nat           347 hands inside 2m..8m, sorted by wait mask

A code (t0,t1,t2,t3) is encoded as t0 + 64 t1 + 64^2 t2 + 64^3 t3.
"""
import sys, os

NAMES = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","7p","8p","9p",
         "1s","2s","3s","4s","5s","6s","7s","8s","9s","E","S","W","N","P","F","C"]
IDX = {n: i for i, n in enumerate(NAMES)}


def enc(c):
    return c[0] + 64 * c[1] + 4096 * c[2] + 262144 * c[3]


def load_plan(path):
    rows = []
    for line in open(path):
        a = line.split()
        if not a:
            continue
        mask = int(a[0], 16); n = int(a[1]); k = int(a[2]); xs = list(map(int, a[3:]))
        assert k == 4 and len(xs) == 4 * n
        rows.append((mask, [xs[4 * i:4 * i + 4] for i in range(n)]))
    return rows


def emit_tree(f, name, items, value_fmt, prefix):
    """balanced BST over sorted (key, value) items; one def per node"""
    defs = []

    def go(lo, hi):
        if lo >= hi:
            return 'PTree.leaf'
        mid = (lo + hi) // 2
        L = go(lo, mid)
        R = go(mid + 1, hi)
        k, v = items[mid]
        nm = f'{prefix}{mid}'
        defs.append(f'def {nm} : PTree {value_fmt[0]} := PTree.node {L} {k} {value_fmt[1](v)} {R}')
        return nm

    root = go(0, len(items))
    f.write('\n'.join(defs))
    f.write(f'\n\ndef {name} : PTree {value_fmt[0]} := {root}\n')


def main(plan_path, cert_path, outdir):
    rows = load_plan(plan_path)
    rows.sort(key=lambda r: r[0])
    os.makedirs(os.path.join(outdir, 'Tenpai', 'Data'), exist_ok=True)
    hdr = 'namespace Tenpai' + chr(10) + chr(10)
    IMPORT = 'import Tenpai.Checks' + chr(10) + chr(10)
    # class tree
    with open(os.path.join(outdir, 'Tenpai/Data/ClassTree.lean'), 'w', encoding='utf-8') as f:
        f.write(IMPORT)
        f.write('/-! The k = 4 plan of the original authors (2846 classes, 17,579 ordered codes),\n'
                '    as a search tree: wait mask ↦ encoded codes (same code sets, reordered by usefulness). -/\n')
        f.write(hdr)
        emit_tree(f, 'classTree', [(m, [enc(c) for c in cs]) for m, cs in rows],
                  ('(List Nat)', lambda v: '[' + ', '.join(map(str, v)) + ']'), 'cn')
        f.write('\nend Tenpai\n')
    # decode tree
    dec = {}
    for m, cs in rows:
        for c in cs:
            e = enc(c)
            assert e not in dec, 'duplicate ordered code'
            dec[e] = m
    items = sorted(dec.items())
    with open(os.path.join(outdir, 'Tenpai/Data/DecodeTree.lean'), 'w', encoding='utf-8') as f:
        f.write(IMPORT)
        f.write('/-! The decoding table of the plan: encoded code ↦ wait mask. -/\n')
        f.write(hdr)
        emit_tree(f, 'decodeTree', items, ('Nat', str), 'dn')
        f.write('\nend Tenpai\n')
    # seven-pairs groups (consecutive windows; a pair of tiles is joined iff a code of {z} fits z+xx+yy)
    plan = dict(rows)
    cuts_all = []
    for z in range(34):
        codes = plan[1 << z]

        def edge(x, y):
            hand = [0] * 34
            hand[z] += 1; hand[x] += 2; hand[y] += 2
            for c in codes:
                need = [0] * 34
                for t in c:
                    need[t] += 1
                if all(need[t] <= hand[t] for t in range(34)):
                    return True
            return False

        cuts, members = [], []
        for t in range(34):
            if t == z:
                continue
            if members and all(edge(m, t) for m in members):
                members.append(t)
            else:
                if members:
                    cuts.append(t)
                members = [t]
        assert len(cuts) <= 4, (z, cuts)
        cuts_all.append(cuts)
    with open(os.path.join(outdir, 'Tenpai/Data/Cuts.lean'), 'w', encoding='utf-8') as f:
        f.write(IMPORT)
        f.write('/-! Seven pairs: for each single `z`, the other 33 tiles are cut into ≤ 5 consecutive groups. -/\n')
        f.write(hdr)
        f.write('def cutsTable : List (List Nat) := [\n  ' +
                ',\n  '.join('[' + ', '.join(map(str, c)) + ']' for c in cuts_all) + ']\n\n')
        f.write('def cutsOf (z : Nat) : List Nat := cutsTable.getD z []\n\nend Tenpai\n')
    # witnesses
    wits = []
    for line in open(cert_path, encoding='utf-8'):
        if line.startswith('#') or not line.strip():
            continue
        wset, hand = line.rstrip('\n').split('\t')
        mask = 0
        for nm in wset.split(','):
            mask |= 1 << IDX[nm]
        cnt = [0] * 9
        i = 0
        while i < len(hand):
            r = int(hand[i]); assert hand[i + 1] == 'm'
            cnt[r - 1] += 1; i += 2
        u = sum(cnt[j] << (4 * j) for j in range(9))
        wits.append((mask, u))
    wits.sort()
    assert len(wits) == 347 and len(set(m for m, _ in wits)) == 347
    with open(os.path.join(outdir, 'Tenpai/Data/Witness.lean'), 'w', encoding='utf-8') as f:
        f.write(IMPORT)
        f.write('/-! 347 hands inside 2m … 8m with pairwise different wait sets (sorted by wait mask). -/\n')
        f.write(hdr)
        f.write('def witnesses : List Nat := [\n  ' + ',\n  '.join(str(u) for _, u in wits) + ']\n\nend Tenpai\n')
    print('classes', len(rows), 'codes', len(dec), 'cuts', [len(c) for c in cuts_all][:5], 'witnesses', len(wits))


if __name__ == '__main__':
    main(*sys.argv[1:4])
