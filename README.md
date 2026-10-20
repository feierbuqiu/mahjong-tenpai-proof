# mahjong-tenpai-proof

**A kernel-checked Lean 4 proof that four tiles suffice, and fewer do not, for the mahjong tenpai wait-set encoding puzzle (*k*\* = 4).**

## The puzzle

A player holds a legal 13-tile Japanese (riichi) mahjong hand that is one tile away from winning (*tenpai*). The two players agree on a rule in advance:
1. The player lays all 13 tiles face down in an order of their choosing.
2. A partner turns over *k* of them.
3. The partner must then name **exactly** the set of tiles that would complete the hand (its *wait set*).

What is the least *k* for which one agreed rule works for every legal tenpai hand?

**Answer: *k*\* = 4.** This repository contains a complete, end-to-end formal proof of that answer, checked by the Lean 4 kernel, together with all supporting material.

```lean
theorem Tenpai.kStar_eq_four : Tenpai.IsKStar 4
-- 'Tenpai.kStar_eq_four' depends on axioms: [propext, Classical.choice, Quot.sound]
```

## Who did what

This repository brings together the work of several people. Every part is credited to its author.

| Contribution | By | Where |
|---|---|---|
| The original puzzle | **Lingzhi Shenpanzhe (Bilibili user 零之审判者)**, in a Bilibili post | <https://www.bilibili.com/opus/1246853448736964611> |
| The precise problem statement (definitions, two viewing models and their equivalence) | **feierbuqiu** | [`docs/problem-statement.md`](docs/problem-statement.md) (English translation) and the [Chinese original](docs/呆饼问题（二）：听牌信息的排列编码问题.md) |
| The computation, the construction and the answer *k*\* = 4 (exhaustive search, the 2,846-class / 17,579-code encoding plan, the lower-bound argument, their own Python verifiers and a Lean attempt) | **Qianwan Dangliang (Bilibili user 千万当量)**, posted in reply to the Bilibili puzzle and originally shared on Baidu Netdisk: <https://pan.baidu.com/s/1qdCW0N75TZzIRsUYx-75Tw?pwd=utfx> | [`third_party/qianwan-dangliang/`](third_party/qianwan-dangliang/), mirrored unmodified (see [`third_party/README.md`](third_party/README.md)) |
| The kernel-only Lean 4 formal proof, the independent cross-check of the computation and the paper | **feierbuqiu**, with AI assistance (Claude Code, Claude Opus 5.5) | [`claude_independent_review/`](claude_independent_review/) |

**Scope of the formal proof.** It uses Qianwan Dangliang's encoding plan as an untrusted *certificate*: every property of the plan that the answer needs is re-checked by the Lean kernel. The original solution process and construction were not modified.

## Repository layout

| Path | Contents |
|---|---|
| [`claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md`](claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md) | **The paper**: what was proved, how, how it was verified and how to reproduce it |
| [`claude_independent_review/lean_formal/lean_project/`](claude_independent_review/lean_formal/lean_project/) | The Lean 4 project (126 Lean files). The trusted statement is the 91-line [`Tenpai/Spec.lean`](claude_independent_review/lean_formal/lean_project/Tenpai/Spec.lean) |
| [`claude_independent_review/lean_formal/tools/`](claude_independent_review/lean_formal/tools/) | Generators for the data and the 1,075 kernel-checked leaves, the split planner, the source-manifest tool |
| [`claude_independent_review/lean_formal/logs/`](claude_independent_review/lean_formal/logs/) | Build evidence: from-scratch build log, source manifests, acceptance-gate tests, calibration runs |
| [`claude_independent_review/lean_formal/ci/`](claude_independent_review/lean_formal/ci/) | A GitHub Actions workflow template for re-running the proof online (not active) |
| [`claude_independent_review/src/`](claude_independent_review/src/), [`claude_independent_review/out/`](claude_independent_review/out/) | Independent cross-check (C and Python) of the computation, and its outputs |
| [`docs/`](docs/) | Problem statement and documentation |
| [`third_party/`](third_party/) | Qianwan Dangliang's original package, unmodified, with a checksum list |

## Verify it yourself

You need [elan](https://github.com/leanprover/elan), the Lean toolchain manager. The toolchain itself (Lean 4.35.0) is pinned by the project and installed automatically.

```bash
cd claude_independent_review/lean_formal/lean_project
lake build
```

- **Success is the acceptance check.** The project ends with an acceptance gate (`#guard_msgs` on `#print axioms`), so the build fails unless the final theorem depends on exactly Lean's three standard axioms. Any `sorry` or extra axiom therefore makes it fail.
- **Expected cost.** About 22 minutes on a 16-thread, 32 GB machine, with peak memory of about 12 GB in total.
- **More.** See [`docs/reproducing.md`](docs/reproducing.md) for source-identity checks, regenerating every generated file and online re-execution.

## Documentation

- [`docs/README.md`](docs/README.md): documentation index
- [`docs/problem-statement.md`](docs/problem-statement.md): the problem, precisely
- [`docs/proof-overview.md`](docs/proof-overview.md): how the proof is structured
- [`docs/reproducing.md`](docs/reproducing.md): reproducing every result
- [`docs/provenance.md`](docs/provenance.md): where every file came from

## Licence

- **The repository's own work** (everything outside `third_party/`) is released under the [MIT Licence](LICENSE).
- **Third-party material** in `third_party/` is **not** covered by the MIT Licence. It remains the work of its author and is mirrored for archival and reference.
- **Derived data.** Some files in `claude_independent_review/` contain Qianwan Dangliang's encoding plan in converted form.

See [`NOTICE.md`](NOTICE.md) for the exact scope.

## Contributing, security and conduct

- [`CONTRIBUTING.md`](CONTRIBUTING.md): how to contribute. **All commits on every branch must be signed and show as Verified**; unsigned commits are rejected by a repository ruleset.
- [`SECURITY.md`](SECURITY.md): how to report a soundness problem, an integrity problem or a privacy problem.
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md): expected behaviour in this project.

## Citation

See [`CITATION.cff`](CITATION.cff), or cite:

> feierbuqiu. (2026). *Four tiles suffice: A kernel-only, end-to-end Lean 4 formalisation of the optimal encoding length for mahjong wait sets*. GitHub. https://github.com/feierbuqiu/mahjong-tenpai-proof

Please also credit Lingzhi Shenpanzhe (零之审判者) for the original puzzle, and Qianwan Dangliang (千万当量) for the computation and construction.
