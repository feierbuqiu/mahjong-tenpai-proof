"""Regenerate every generated file from its inputs and compare it with the committed file.

usage: python -I claude_independent_review/lean_formal/tools/check_regeneration.py   (from the repository root)

Checks, each of which must pass:
  1. gen_data.py rebuilds Tenpai/Data/{ClassTree,DecodeTree,Cuts,Witness}.lean byte for byte;
  2. gen_split.py rebuilds every file of Tenpai/Run/ (same file set) and Tenpai/Main.lean byte for byte;
  3. the original plan third_party/qianwan-dangliang/work/verify/plan_k4_final.json has its published SHA-256,
     and src/plan_json_to_txt.py converts it to out/their_plan_k4_FINAL.txt byte for byte;
  4. tools/plan_k4_reordered.txt (the input of gen_data.py) has the same classes as the original plan, and for
     each class the same multiset of ordered codes: codes were reordered within classes only.
Nothing in the repository is modified; all output goes to a temporary directory.
Exit code: 0 if every check passes, 1 otherwise.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

CIR = 'claude_independent_review'
LF = os.path.join(CIR, 'lean_formal')
LP = os.path.join(LF, 'lean_project')
TOOLS = os.path.join(LF, 'tools')
PLAN_JSON = os.path.join('third_party', 'qianwan-dangliang', 'work', 'verify', 'plan_k4_final.json')
PLAN_JSON_SHA256 = 'b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163'
NCHAINS = '6'

failures = []


def same_bytes(a, b):
    with open(a, 'rb') as x, open(b, 'rb') as y:
        return x.read() == y.read()


def run(args, cwd=None):
    r = subprocess.run([sys.executable, '-I'] + args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        failures.append(f'{os.path.basename(args[0])} exited with {r.returncode}: {r.stderr.strip()[-300:]}')
    return r.returncode == 0


def compare_tree(new_dir, old_dir, label):
    new = sorted(os.listdir(new_dir))
    old = sorted(os.listdir(old_dir))
    if new != old:
        failures.append(f'{label}: file sets differ (only new: {sorted(set(new) - set(old))[:5]}, '
                        f'only committed: {sorted(set(old) - set(new))[:5]})')
    diff = [f for f in new if f in old and not same_bytes(os.path.join(new_dir, f), os.path.join(old_dir, f))]
    if diff:
        failures.append(f'{label}: {len(diff)} file(s) differ, e.g. {diff[:5]}')
    return len(new), len(diff)


def read_plan(path):
    """class mask -> Counter of ordered codes"""
    plan = {}
    with open(path, encoding='ascii') as f:
        for line in f:
            a = line.split()
            if not a:
                continue
            mask, n, k = a[0], int(a[1]), int(a[2])
            nums = a[3:]
            if len(nums) != n * k:
                failures.append(f'{path}: class {mask} has {len(nums)} numbers, expected {n * k}')
            codes = [tuple(nums[i * k:(i + 1) * k]) for i in range(n)]
            if mask in plan:
                failures.append(f'{path}: class {mask} appears twice')
            plan[mask] = Counter(codes)
    return plan


def main():
    with tempfile.TemporaryDirectory() as tmp:
        # 1. data modules
        out = os.path.join(tmp, 'data')
        if run([os.path.join(TOOLS, 'gen_data.py'), os.path.join(TOOLS, 'plan_k4_reordered.txt'),
                os.path.join(CIR, 'out', 'u7_certificate.txt'), out]):
            n, d = compare_tree(os.path.join(out, 'Tenpai', 'Data'), os.path.join(LP, 'Tenpai', 'Data'), 'Tenpai/Data')
            print(f'[1] gen_data.py: {n} data modules regenerated, {d} differ')
        # 2. check modules and Main.lean (gen_split.py works in a copy of the project)
        proj = os.path.join(tmp, 'project')
        shutil.copytree(LP, proj, ignore=shutil.ignore_patterns('.lake'))
        if run([os.path.abspath(os.path.join(TOOLS, 'gen_split.py')), os.path.abspath(os.path.join(TOOLS, 'split.txt')),
                NCHAINS], cwd=proj):
            n, d = compare_tree(os.path.join(proj, 'Tenpai', 'Run'), os.path.join(LP, 'Tenpai', 'Run'), 'Tenpai/Run')
            main_ok = same_bytes(os.path.join(proj, 'Tenpai', 'Main.lean'), os.path.join(LP, 'Tenpai', 'Main.lean'))
            if not main_ok:
                failures.append('Tenpai/Main.lean differs')
            print(f'[2] gen_split.py: {n} check modules regenerated, {d} differ; Main.lean '
                  f'{"identical" if main_ok else "DIFFERS"}')
        # 3. original plan: hash and conversion
        with open(PLAN_JSON, 'rb') as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest != PLAN_JSON_SHA256:
            failures.append(f'{PLAN_JSON}: SHA-256 {digest} is not the published one')
        txt = os.path.join(tmp, 'their_plan.txt')
        conv_ok = False
        if run([os.path.join(CIR, 'src', 'plan_json_to_txt.py'), PLAN_JSON, txt]):
            conv_ok = same_bytes(txt, os.path.join(CIR, 'out', 'their_plan_k4_FINAL.txt'))
            if not conv_ok:
                failures.append('out/their_plan_k4_FINAL.txt differs from the conversion of the original plan')
        print(f'[3] original plan: SHA-256 {"matches" if digest == PLAN_JSON_SHA256 else "DIFFERS"}; '
              f'conversion {"identical to out/their_plan_k4_FINAL.txt" if conv_ok else "DIFFERS"}')
    # 4. reordering is within classes only
    original = read_plan(os.path.join(CIR, 'out', 'their_plan_k4_FINAL.txt'))
    reordered = read_plan(os.path.join(TOOLS, 'plan_k4_reordered.txt'))
    bad = [m for m in original if reordered.get(m) != original[m]]
    if set(original) != set(reordered):
        failures.append('the reordered plan does not have the same classes as the original plan')
    if bad:
        failures.append(f'{len(bad)} class(es) have different code multisets after reordering, e.g. {bad[:3]}')
    print(f'[4] reordered plan: {len(reordered)} classes, {sum(sum(c.values()) for c in reordered.values())} codes; '
          f'same classes and per-class code multisets: {"yes" if not bad and set(original) == set(reordered) else "NO"}')
    for f in failures:
        print('FAIL:', f)
    print('REGENERATION:', 'OK' if not failures else 'FAILED')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
