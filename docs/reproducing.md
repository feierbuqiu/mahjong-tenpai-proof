# Reproducing the Results

These instructions describe [release v1](https://github.com/feierbuqiu/mahjong-tenpai-proof/releases/tag/v1). All commands are run from the repository root unless stated otherwise.

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

and ends with `Build completed successfully`. A successful build is the acceptance check: an acceptance gate at the end of [`Tenpai/Main.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Main.lean) fails the build if the final theorem's axiom list differs in any way. The gate covers everything the final theorem depends on, directly or indirectly; declarations it does not use are outside its scope.

**Resources.** On a 16-thread, 32 GB machine the build takes about 22 minutes. The 97 generated check modules form six import chains, so at most six of them are checked at once. Peak memory was about 12 GB in total and about 5 GB for one process.

**Recorded evidence** is in [`claude_independent_review/lean_formal/logs/`](../claude_independent_review/lean_formal/logs/):

| Path | Contents |
|---|---|
| [`clean_build/`](../claude_independent_review/lean_formal/logs/clean_build/) | the authoritative local from-scratch build: log, timing, memory samples, source manifests before and after, axiom printout |
| [`ci_build/`](../claude_independent_review/lean_formal/logs/ci_build/) | the online from-scratch build on GitHub Actions: runner details, log, timing, memory samples, source manifest |
| [`first_build/`](../claude_independent_review/lean_formal/logs/first_build/) | an earlier full build |
| [`gate_tests/`](../claude_independent_review/lean_formal/logs/gate_tests/) | tests showing that the gate rejects `sorry` and extra axioms in the final theorem's dependencies |
| [`calibration_runs.txt`](../claude_independent_review/lean_formal/logs/calibration_runs.txt) | single-leaf calibration measurements |

The one path-bearing log line in `gate_tests/` has been redacted (`<build-dir>`, `<home>`).

## 2. Check that the sources are the published ones

```bash
python -I claude_independent_review/lean_formal/tools/manifest.py claude_independent_review/lean_formal/lean_project out.json
```

Two fields of `out.json` must have these values:

| Field | Covers | Value |
|---|---|---|
| `lean_set_sha256` | the 126 Lean files | `a179bd53953a21dc4b38489f9cc13e10c698a23b034555ae413b85e68ef191d2` |
| `all_sha256` | the Lean files and the build configuration (`lakefile.toml`, `lean-toolchain`, `lake-manifest.json`) | `9ec53ef1a446d582e59729f97eea4f9f54e2938466acbdcce84216b8075fd7e6` |

These are the digests recorded before and after the authoritative build in [`logs/clean_build/`](../claude_independent_review/lean_formal/logs/clean_build/) and in the online build.

**Line endings.** The repository stores every file byte for byte ([`.gitattributes`](../.gitattributes) disables line-ending conversion), so the digests are the same on every platform.

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

The outputs are byte-identical to the published files on every platform.

**Checking it without touching the repository.** [`check_regeneration.py`](../claude_independent_review/lean_formal/tools/check_regeneration.py) does steps 1 and 3 in a temporary directory and compares every output with the committed file. It also checks the provenance of the plan:
- the original plan has its published SHA-256;
- converting it to text reproduces `out/their_plan_k4_FINAL.txt`;
- the plan used by the proof differs from it only by the order of codes within each class.

```bash
python -I claude_independent_review/lean_formal/tools/check_regeneration.py
```

**Building the C tools.** `plan_split` and the other C programs are distributed as source only. They were written for, and built on, Windows with the `clang` bundled in the Lean toolchain. That compiler ships without C library headers, so [`claude_independent_review/src/minic.h`](../claude_independent_review/src/minic.h) declares the few C library and Windows thread functions the programs use. The build command was:

```bash
TC=~/.elan/toolchains/leanprover--lean4---v4.35.0
$TC/bin/clang -O2 -march=native -ffreestanding -isystem $TC/include/clang plan_split.c -o plan_split.exe
```

## 4. Re-run the independent cross-check

The C and Python programs in [`claude_independent_review/src/`](../claude_independent_review/src/) independently re-derive the computational results:
- the census of all tenpai hands and their 2,846 wait classes;
- the lower-bound counts;
- an independent four-tile plan, checked against every hand together with the original plan.

Their recorded outputs are in [`claude_independent_review/out/`](../claude_independent_review/out/). Build them the same way, into `claude_independent_review/`:

```bash
cd claude_independent_review/src
for p in census completeness g_sources build; do
  $TC/bin/clang -O2 -march=native -ffreestanding -isystem $TC/include/clang -Wall -Wno-unused-function $p.c -o ../$p.exe
done
cd .. && bash src/recheck.sh
```

**What `recheck.sh` does.** [`src/recheck.sh`](../claude_independent_review/src/recheck.sh) re-runs every program and compares each output with its recorded log, ignoring timing. It also runs negative tests: invalid thread counts, a plan with a missing class, and a plan with an out-of-range tile. It exits with a non-zero code on any difference. [`out/recheck.log`](../claude_independent_review/out/recheck.log) is its local run.

**Exit codes.** Each program exits with a non-zero code, and prints `RESULT: FAILED`, when a check fails or when not every work item of the enumeration was processed.

## 5. Online re-execution (continuous integration)

The checks also run on GitHub Actions. All runners are GitHub's standard runners for public repositories; the Linux runner has 4 CPUs and 16 GB of RAM.

| Workflow | When it runs | What it does |
|---|---|---|
| [`lean-kernel-build.yml`](../.github/workflows/lean-kernel-build.yml) | whenever the Lean sources change, and on demand from the *Actions* tab | checks the source and configuration digests, installs the pinned toolchain, runs `lake build` from scratch (the acceptance gate decides the outcome) and keeps the log, timing and memory samples as a run artefact |
| [`integrity.yml`](../.github/workflows/integrity.yml) | on every push and pull request | checks that the third-party mirror is byte-for-byte unchanged, with no file added or removed; checks that the Lean sources and the build configuration match their digests; runs `check_regeneration.py` |
| [`cross-check.yml`](../.github/workflows/cross-check.yml) | whenever the cross-check programs or their recorded outputs change, and on demand | builds the cross-check programs on Windows with the Lean toolchain's `clang` and runs `src/recheck.sh` |
| [`codeql.yml`](../.github/workflows/codeql.yml) | on every push to `main`, on every pull request, and weekly | CodeQL code scanning of the workflows, the Python tools and the C programs (the verbatim third-party mirror is excluded); results appear in the *Security* tab |

**Recorded run.** The [run of 20 October 2026](https://github.com/feierbuqiu/mahjong-tenpai-proof/actions/runs/39360643654) completed the build in 31 minutes 37 seconds, with a combined memory peak of 9.5 GB (5.0 GB for one process). Its log, timing, memory samples and runner details are kept in [`logs/ci_build/`](../claude_independent_review/lean_formal/logs/ci_build/).

**Running it yourself.** Fork the repository and start the workflows from the fork's *Actions* tab. They need no secrets.

**Template.** The kernel-build workflow was adapted from [`claude_independent_review/lean_formal/ci/lean-kernel-build.yml`](../claude_independent_review/lean_formal/ci/lean-kernel-build.yml), which expects `lean_project/` and `tools/` at the root of the repository it runs in.

## 6. Re-check with another kernel (optional)

Lean's documentation describes `lean4checker`, which replays stored declarations through the kernel. It also describes comparison tooling that can use the independent checker *nanoda*. The proof uses no native evaluation, so it is eligible for both. Neither has been run for release v1.
