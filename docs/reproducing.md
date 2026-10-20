# Reproducing the Results

All commands are run from the repository root unless stated otherwise.

## 1. Re-run the kernel check

Requirement: [elan](https://github.com/leanprover/elan). The Lean toolchain (4.35.0) is pinned in [`lean-toolchain`](../claude_independent_review/lean_formal/lean_project/lean-toolchain) and installed automatically.

```bash
cd claude_independent_review/lean_formal/lean_project
lake build
```

**Expected result.** The log contains

```text
'Tenpai.kStar_eq_four' depends on axioms: [propext, Classical.choice, Quot.sound]
```

and ends with `Build completed successfully`. A successful build is the acceptance check: an acceptance gate at the end of [`Tenpai/Main.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Main.lean) fails the build if the axiom list differs in any way.

**Resources.** On a 16-thread, 32 GB machine the build takes about 22 minutes. The 97 generated check modules form six import chains, so at most six of them are checked at once. Peak memory was about 12 GB in total and about 5 GB for one process.

**Recorded evidence** is in [`claude_independent_review/lean_formal/logs/`](../claude_independent_review/lean_formal/logs/):

| Path | Contents |
|---|---|
| [`clean_build/`](../claude_independent_review/lean_formal/logs/clean_build/) | the authoritative from-scratch build: log, timing, memory samples, source manifests before and after, axiom printout |
| [`first_build/`](../claude_independent_review/lean_formal/logs/first_build/) | an earlier full build |
| [`gate_tests/`](../claude_independent_review/lean_formal/logs/gate_tests/) | tests showing that the gate rejects `sorry` and extra axioms |
| [`calibration_runs.txt`](../claude_independent_review/lean_formal/logs/calibration_runs.txt) | single-leaf calibration measurements |

The one path-bearing log line in `gate_tests/` has been redacted (`<build-dir>`, `<home>`).

## 2. Check that the sources are the published ones

```bash
python -I claude_independent_review/lean_formal/tools/manifest.py claude_independent_review/lean_formal/lean_project out.json
```

The field `lean_set_sha256` must equal

```text
a179bd53953a21dc4b38489f9cc13e10c698a23b034555ae413b85e68ef191d2
```

That is the digest of the sources recorded before and after the authoritative build in [`logs/clean_build/`](../claude_independent_review/lean_formal/logs/clean_build/).

**Line endings.** The repository stores every file byte for byte ([`.gitattributes`](../.gitattributes) disables line-ending conversion), so the digest is the same on every platform.

## 3. Regenerate the generated files

These commands are run from `claude_independent_review/`.

```bash
python -I lean_formal/tools/gen_data.py lean_formal/tools/plan_k4_reordered.txt out/u7_certificate.txt lean_formal/lean_project
cd lean_formal/lean_project
../tools/plan_split.exe ../tools/split.txt 12
python -I ../tools/gen_split.py ../tools/split.txt 6
```

**What they do:**
1. [`gen_data.py`](../claude_independent_review/lean_formal/tools/gen_data.py) regenerates the four data modules in [`Tenpai/Data/`](../claude_independent_review/lean_formal/lean_project/Tenpai/Data/).
2. `plan_split`, built from [`plan_split.c`](../claude_independent_review/lean_formal/tools/plan_split.c), regenerates the split plan [`split.txt`](../claude_independent_review/lean_formal/tools/split.txt).
3. [`gen_split.py`](../claude_independent_review/lean_formal/tools/gen_split.py) regenerates the 97 check modules in [`Tenpai/Run/`](../claude_independent_review/lean_formal/lean_project/Tenpai/Run/) and `Tenpai/Main.lean`.

The outputs are byte-identical to the published files.

**Building the C tools.** `plan_split` and the other C programs are distributed as source only. They were written for, and built on, Windows with the `clang` bundled in the Lean toolchain. That compiler ships without C library headers, so [`claude_independent_review/src/minic.h`](../claude_independent_review/src/minic.h) declares the few C library and Windows thread functions the programs use. The build command was:

```bash
TC=~/.elan/toolchains/leanprover--lean4---v4.35.0
$TC/bin/clang -O2 -march=native -ffreestanding -isystem $TC/include/clang plan_split.c -o plan_split.exe
```

## 4. Re-run the independent cross-check

The C and Python programs in [`claude_independent_review/src/`](../claude_independent_review/src/) independently re-derive the computational results: the census of all tenpai hands, the 2,846 wait classes, the lower-bound counts, and an independent four-tile plan checked against every hand. Their recorded outputs are in [`claude_independent_review/out/`](../claude_independent_review/out/). Build them the same way, for example:

```bash
cd claude_independent_review/src
$TC/bin/clang -O2 -march=native -ffreestanding -isystem $TC/include/clang census.c -o ../census.exe
```

## 5. Online re-execution

[`claude_independent_review/lean_formal/ci/lean-kernel-build.yml`](../claude_independent_review/lean_formal/ci/lean-kernel-build.yml) is a GitHub Actions workflow template. It has not yet been run online.

**What it does:**
1. installs elan;
2. checks the source digest;
3. runs `lake build`;
4. keeps the log.

**Using it.** The template expects `lean_project/` and `tools/` at the root of the repository it runs in. To use it here, copy it to `.github/workflows/` and prefix its paths with `claude_independent_review/lean_formal/`.

**Runner size.** GitHub's standard Linux runner for public repositories has 4 CPUs and 16 GB of RAM, which should fit the measured peak of about 12 GB.

## 6. Re-check with another kernel (optional)

Lean's documentation describes `lean4checker`, which replays stored declarations through the kernel. It also describes comparison tooling that can use the independent checker *nanoda*. The proof uses no native evaluation, so it is eligible for both.
