"""Generate the kernel-check modules (from split.txt) and the final assembly `Tenpai/Main.lean`.

usage: python -I gen_split.py <split.txt> <nchains> [stub]

* every leaf of split.txt becomes one theorem `... := by decide +kernel` (evaluated by the kernel);
* leaves are spread over <nchains> import chains (`Tenpai/Run/K<c>_<i>.lean`, each module importing
  the previous one of its chain), so at most <nchains> Lean processes run at once;
* `Tenpai/Main.lean` rebuilds the prefix trees (T1, T2) and the shape ranges (T4), assembles
  `Checked classTree cutsOf` and proves `kStar_eq_four : IsKStar 4`; it ends with an acceptance
  gate (`#guard_msgs` on `#print axioms`) that fails the build unless the final theorem depends on
  exactly `propext`, `Classical.choice`, `Quot.sound`.
With `stub`, the leaves are `sorry` (only to test the assembly quickly).  A stub project is marked
as such in every generated module and can never build successfully: its `sorryAx` trips the gate.
"""
import sys, os, random

split_path, nchains = sys.argv[1], int(sys.argv[2])
STUB = len(sys.argv) > 3 and sys.argv[3] == 'stub'
MODULE_BUDGET = 60.0  # estimated seconds of kernel work per module

leaves = []   # (name, statement, cost)

def add(name, stmt, cost):
    leaves.append((name, stmt, cost))

add('decode_ok', 'decodeOK classTree decodeTree = true', 10.0)
add('t0_ok', 't0ok classTree = true', 5.0)
add('t3_ok', 't3ok classTree cutsOf = true', 11.0)
add('k_ok', 'kOK classTree = true', 35.0)
add('wit_ok', 'witOK witnesses = true', 12.0)
add('wit_len', 'witnesses.length = 347', 0.1)

def catlen(k):
    return 9 if k < 3 else 7

def pname(digits):
    return 'p' + ''.join(str(d) for d in digits)

def node_args(L, n, digits):
    """(m, r, acc, mul) of the prefix node"""
    j = len(digits)
    acc = sum(d * 16 ** i for i, d in enumerate(digits))
    return L - j, n - sum(digits), acc, 16 ** j

t1_leaves = {}   # (k, n) -> set of digit tuples
t2_leaves = {}   # (x, y, nx, ny, rev) -> set of digit tuples
t4a = {}         # x -> [(lo, hi)]
t4b = {}         # (x, y) -> [(lo, hi)]

def t1fun(k, n):
    return f't1unit classTree {k} {n}'

def t2fun(x, y, nx, ny, rev):
    if rev:
        return f't2outerRev classTree {x} {y} {nx} {ny} (innerL {x} {nx})'
    return f't2outer classTree {x} {y} {nx} {ny} (innerL {y} {ny})'

for line in open(split_path):
    a = line.split()
    if not a:
        continue
    if a[0] == 'T1':
        k, n = int(a[1]), int(a[2]); cost = float(a[3]); digits = tuple(map(int, a[4:]))
        t1_leaves.setdefault((k, n), set()).add(digits)
        m, r, acc, mul = node_args(catlen(k), n, digits)
        add(f'T1_{k}_{n}_{pname(digits)}', f'allVecs ({t1fun(k, n)}) {m} {r} {acc} {mul} = true', cost)
    elif a[0] == 'T2':
        x, y, nx, ny, rev = map(int, a[1:6]); cost = float(a[6]); digits = tuple(map(int, a[7:]))
        t2_leaves.setdefault((x, y, nx, ny, rev), set()).add(digits)
        L = catlen(y if rev else x); nout = ny if rev else nx
        m, r, acc, mul = node_args(L, nout, digits)
        add(f'T2_{x}_{y}_{nx}_{ny}_{pname(digits)}', f'allVecs ({t2fun(x, y, nx, ny, rev)}) {m} {r} {acc} {mul} = true', cost)
    elif a[0] == 'T4A':
        x, lo, hi = map(int, a[1:4]); cost = float(a[4])
        t4a.setdefault(x, []).append((lo, hi))
        add(f'T4A_{x}_{lo}', f'forShapesR (pA classTree {x}) {lo} {hi} = true', cost)
    elif a[0] == 'T4B':
        x, y, lo, hi = map(int, a[1:5]); cost = float(a[5])
        t4b.setdefault((x, y), []).append((lo, hi))
        add(f'T4B_{x}_{y}_{lo}', f'forShapesR (pB classTree {x} {y}) {lo} {hi} = true', cost)

# ---------------- chains and modules ----------------
chains = [[] for _ in range(nchains)]
load = [0.0] * nchains
for it in sorted(leaves, key=lambda t: -t[2]):
    c = min(range(nchains), key=lambda j: load[j])
    chains[c].append(it)
    load[c] += it[2]
rng = random.Random(20261020)
for ch in chains:
    rng.shuffle(ch)   # heavy leaves should not all run at the same time

os.makedirs('Tenpai/Run', exist_ok=True)
for f in os.listdir('Tenpai/Run'):
    os.remove(os.path.join('Tenpai/Run', f))
HDR = ('import Tenpai.Data.ClassTree\nimport Tenpai.Data.DecodeTree\nimport Tenpai.Data.Cuts\n'
       'import Tenpai.Data.Witness\nimport Tenpai.Enum\n')
prf = 'sorry' if STUB else 'by decide +kernel'
lasts, nmods = [], 0
for c, its in enumerate(chains):
    mods, cur, cost = [], [], 0.0
    for it in its:
        if cur and cost + it[2] > MODULE_BUDGET:
            mods.append(cur); cur, cost = [], 0.0
        cur.append(it); cost += it[2]
    if cur:
        mods.append(cur)
    prev = None
    for i, group in enumerate(mods):
        mod = f'K{c}_{i:03d}'
        with open(f'Tenpai/Run/{mod}.lean', 'w', encoding='utf-8', newline='\n') as f:
            f.write(HDR if prev is None else f'import Tenpai.Run.{prev}\n')
            if STUB:
                f.write('\n-- STUB MODULE (gen_split.py stub mode): the theorems below are `sorry`, NOT a proof.\n'
                        '-- The acceptance gate at the end of `Tenpai/Main.lean` makes such a build fail.\n')
            f.write('\n/-! Kernel checks (generated by `gen_split.py`; each theorem is evaluated by the kernel). -/\n\n')
            f.write('namespace Tenpai\n\n')
            for (name, stmt, _) in group:
                f.write(f'set_option maxHeartbeats 0 in\ntheorem {name} : {stmt} := {prf}\n\n')
            f.write('end Tenpai\n')
        prev = mod
        nmods += 1
    lasts.append(prev)
with open('Tenpai/Run/All.lean', 'w', encoding='utf-8', newline='\n') as f:
    f.write(''.join(f'import Tenpai.Run.{m}\n' for m in lasts))

# ---------------- the assembly ----------------
out = []
w = out.append
w('import Tenpai.Run.All\nimport Tenpai.Final\nimport Tenpai.EnumSound\n\n')
w('/-!\n# Main theorem: `k* = 4`\n\n'
  'The leaves `Tenpai.Run.*` (each proved by `decide +kernel`, i.e. evaluated by the Lean kernel) are\n'
  'assembled here:\n'
  '* T1 / T2: the prefix trees of `allVecs` (`allVecs_node` joins the five values of the next field);\n'
  '* T4: consecutive ranges of shapes (`forShapesR_merge`, `forShapes_of_R`);\n'
  'then `Checked classTree cutsOf` and, with the decoding table and the 347 lower-bound witnesses,\n'
  '`kStar_eq_four : IsKStar 4`.  This file is generated by `gen_split.py`.\n-/\n\n')
w('namespace Tenpai\n\n')

def emit_tree(prefix, F, L, n, leafset):
    """emit node theorems for all internal prefixes; returns the root theorem name"""
    internal = set()
    for dg in leafset:
        for j in range(len(dg)):
            internal.add(dg[:j])
    assert not (internal & leafset), (prefix, 'leaf is also internal')
    # every internal node must have all its valid children
    for node in sorted(internal, key=lambda t: (-len(t), t)):
        m, r, acc, mul = node_args(L, n, node)
        lines = [f'theorem {prefix}_{pname(node)} : allVecs ({F}) {m} {r} {acc} {mul} = true :=\n'
                 f'  allVecs_node _ _ _ _ _ fun d hd h1 h2 => by\n'
                 f'    rcases (show d = 0 ∨ d = 1 ∨ d = 2 ∨ d = 3 ∨ d = 4 by omega) with rfl | rfl | rfl | rfl | rfl']
        for d in range(5):
            if d <= r and r - d <= 4 * (m - 1):
                child = node + (d,)
                assert child in internal or child in leafset, (prefix, child, 'missing child')
                lines.append(f'    · exact {prefix}_{pname(child)}')
            else:
                lines.append('    · omega')
        w('\n'.join(lines) + '\n\n')
    return f'{prefix}_{pname(())}'

for (k, n), ls in sorted(t1_leaves.items()):
    root = emit_tree(f'T1_{k}_{n}', t1fun(k, n), catlen(k), n, ls)
    w(f'theorem t1all_{k}_{n} : ∀ u ∈ vecs (catLen {k}) {n}, t1unit classTree {k} {n} u = true :=\n'
      f'  t1_of_allVecs classTree {k} {n} {root}\n\n')
for (x, y, nx, ny, rev), ls in sorted(t2_leaves.items()):
    L = catlen(y if rev else x); nout = ny if rev else nx
    root = emit_tree(f'T2_{x}_{y}_{nx}_{ny}', t2fun(x, y, nx, ny, rev), L, nout, ls)
    lem = 't2rev_of_allVecs' if rev else 't2_of_allVecs'
    w(f'theorem t2unit_{x}_{y}_{nx}_{ny} : ∀ u ∈ vecs (catLen {x}) {nx}, ∀ v ∈ vecs (catLen {y}) {ny},\n'
      f'    T2unit classTree {x} {y} {nx} {ny} u v :=\n'
      f'  {lem} classTree {x} {y} {nx} {ny} {root}\n\n')

def merge_term(names_ranges, pfun):
    """forShapesR p 0 2744 from consecutive ranges"""
    rs = sorted(names_ranges, key=lambda t: t[1])
    assert rs[0][1] == 0 and rs[-1][2] == 2744
    for (a, b) in zip(rs, rs[1:]):
        assert a[2] == b[1], 'ranges not consecutive'
    term = rs[-1][0]
    for (nm, lo, hi) in reversed(rs[:-1]):
        term = f'(forShapesR_merge _ {lo} {hi} 2744 {nm} {term})'
    return term

for x, rs in sorted(t4a.items()):
    term = merge_term([(f'T4A_{x}_{lo}', lo, hi) for (lo, hi) in rs], None)
    w(f'theorem t4A_{x} : t4okA classTree {x} = true := by\n  rw [t4okA_eq]\n  exact forShapes_of_R _ {term}\n\n')
for (x, y), rs in sorted(t4b.items()):
    term = merge_term([(f'T4B_{x}_{y}_{lo}', lo, hi) for (lo, hi) in rs], None)
    w(f'theorem t4B_{x}_{y} : t4okB classTree {x} {y} = true := by\n  rw [t4okB_eq]\n  exact forShapes_of_R _ {term}\n\n')

PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
PAIR_CASES = ('    rcases (show (x = 0 ∧ y = 1) ∨ (x = 0 ∧ y = 2) ∨ (x = 0 ∧ y = 3) ∨ (x = 1 ∧ y = 2) ∨\n'
              '        (x = 1 ∧ y = 3) ∨ (x = 2 ∧ y = 3) by omega) with\n'
              '      ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩')
w('/-- all finite checks, assembled -/\n')
w('theorem checked : Checked classTree cutsOf where\n')
w('  valid := treeValid_of_decode classTree decodeTree decode_ok\n')
w('  t0 := t0_ok\n')
w('  t1 := by\n    intro k hk n hn u hu\n')
w('    rcases (show k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 by omega) with rfl | rfl | rfl | rfl <;>\n')
w('      rcases hn with rfl | rfl | rfl | rfl\n')
for k in range(4):
    for n in (4, 7, 10, 13):
        w(f'    · exact t1all_{k}_{n} u hu\n')
w('  t2 := by\n    intro x y hxy hy nx ny hnx hny hs u hu v hv\n')
w(PAIR_CASES + ' <;>\n')
w('      rcases hnx with rfl | rfl | rfl | rfl <;> rcases hny with rfl | rfl | rfl | rfl <;>\n')
w('      first | omega | skip\n')
for (x, y) in PAIRS:
    for nx in (2, 5, 8, 11):
        for ny in (2, 5, 8, 11):
            if nx + ny <= 13:
                w(f'    · exact t2unit_{x}_{y}_{nx}_{ny} u hu v hv\n')
w('  t3 := t3_ok\n')
w('  t4A := by\n    intro x hx\n    rcases (show x = 0 ∨ x = 1 ∨ x = 2 ∨ x = 3 by omega) with rfl | rfl | rfl | rfl\n')
for x in range(4):
    w(f'    · exact t4A_{x}\n')
w('  t4B := by\n    intro x y hxy hy\n')
w(PAIR_CASES + '\n')
for (x, y) in PAIRS:
    w(f'    · exact t4B_{x}_{y}\n')
w('  k := k_ok\n\n')
w('/-- **The answer is four**: `k* = 4`, the least number of tiles to show (see `Tenpai.Spec`). -/\n')
w('theorem kStar_eq_four : IsKStar 4 :=\n'
  '  kstar_of_checks classTree decodeTree cutsOf witnesses checked decode_ok wit_ok wit_len\n\n')
w('end Tenpai\n\n')
w('/-! ## Acceptance gate\n\n'
  '`#guard_msgs` fails the build unless `#print axioms` reports exactly Lean\'s three standard\n'
  'axioms for the final theorem.  A `sorry` anywhere in its dependency cone would add `sorryAx`,\n'
  'and any extra axiom would be listed too, so a successful `lake build` is itself the release\n'
  'check.  The second `#print axioms` only repeats the line in the build log. -/\n\n')
w('/-- info: \'Tenpai.kStar_eq_four\' depends on axioms: [propext, Classical.choice, Quot.sound] -/\n'
  '#guard_msgs in\n'
  '#print axioms Tenpai.kStar_eq_four\n\n')
w('#print axioms Tenpai.kStar_eq_four\n')
with open('Tenpai/Main.lean', 'w', encoding='utf-8', newline='\n') as f:
    f.write(''.join(out))
print(f'leaves {len(leaves)}  modules {nmods}  chains {nchains}  {"stub" if STUB else "kernel"}  '
      f'loads {[round(x) for x in load]}  total {round(sum(load))} s')
if STUB:
    print('WARNING: stub mode -- the leaves are `sorry`; this project is NOT a proof and its build fails at the gate')
