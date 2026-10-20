# Notice: Authorship, Attribution and Licence Scope

This repository combines the repository author's own work with third-party material. This notice states, path by path, who made what and which terms apply.

## 1. The repository author's work (MIT Licence)

These parts are by **feierbuqiu** and are released under the [MIT Licence](LICENSE), subject to the derived-data note in §3.

| Path | Contents |
|---|---|
| [`claude_independent_review/`](claude_independent_review/) | The kernel-only Lean 4 formal proof, its generators and tools, its build evidence, the independent cross-check programs and their outputs, and the paper |
| [`docs/`](docs/) | The problem statement (Chinese original and English translation) and the documentation |
| Repository files | [`README.md`](README.md), [`NOTICE.md`](NOTICE.md), [`SECURITY.md`](SECURITY.md), [`CONTRIBUTING.md`](CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), [`CITATION.cff`](CITATION.cff), [`.github/`](.github/), [`.gitignore`](.gitignore), [`.gitattributes`](.gitattributes) |

**AI assistance.** This work was produced with substantial assistance from Anthropic's Claude Code, running the Claude Opus 5.5 model. The correctness of every proof is established by the Lean kernel, not by the AI system. See the paper's Declaration of Generative AI Use.

**The puzzle itself** was first posed by **Lingzhi Shenpanzhe (Bilibili user 零之审判者)** in a Bilibili post: <https://www.bilibili.com/opus/1246853448736964611>. The problem statement in [`docs/`](docs/) is feierbuqiu's precise formulation of that puzzle.

## 2. Third-party material (not covered by the MIT Licence)

**[`third_party/qianwan-dangliang/`](third_party/qianwan-dangliang/)** is the computational study by **Qianwan Dangliang (Bilibili user 千万当量)**. It was posted in reply to Lingzhi Shenpanzhe's Bilibili post above and originally shared on Baidu Netdisk: <https://pan.baidu.com/s/1qdCW0N75TZzIRsUYx-75Tw?pwd=utfx>.

**What it contains:**
- the computation and the construction that established *k*\* = 4;
- the final encoding plan [`work/verify/plan_k4_final.json`](third_party/qianwan-dangliang/work/verify/plan_k4_final.json);
- the author's Python verifiers;
- a web demonstration;
- the author's own Lean attempt.

**Terms:**
- No licence was distributed with the package. All rights remain with its author.
- It is mirrored here without modification, for archival and reference, so that the work is available in a stable, citable place with clear attribution.
- The only change is that one Python bytecode cache directory (`work/lowerbound/__pycache__/`) was not included; the author's own packaging script also excludes such caches.
- [`third_party/qianwan-dangliang.SHA256SUMS`](third_party/qianwan-dangliang.SHA256SUMS) lists the SHA-256 of every mirrored file.
- **If you are the author and want the mirror changed or removed, please open an issue.**

**Images of unknown origin.** The mahjong tile images in [`third_party/qianwan-dangliang/web/pai-images/`](third_party/qianwan-dangliang/web/pai-images/), and the copies embedded in [`third_party/qianwan-dangliang/web/mahjong_demo.html`](third_party/qianwan-dangliang/web/mahjong_demo.html), are described in the author's [`web/README.md`](third_party/qianwan-dangliang/web/README.md) as supplied to the author. Their original source and licence are not documented. Any rights in them remain with their owners. Rights holders may request removal by opening an issue.

## 3. Derived data

The following files contain Qianwan Dangliang's encoding plan, or data computed from it, in converted form. The MIT Licence covers the conversion code and our formatting; the underlying plan remains attributed to its author.

| File | Contents |
|---|---|
| [`claude_independent_review/lean_formal/lean_project/Tenpai/Data/ClassTree.lean`](claude_independent_review/lean_formal/lean_project/Tenpai/Data/ClassTree.lean) | the plan as a Lean search tree (2,846 classes, 17,579 codes; codes reordered within each class only) |
| [`claude_independent_review/lean_formal/lean_project/Tenpai/Data/DecodeTree.lean`](claude_independent_review/lean_formal/lean_project/Tenpai/Data/DecodeTree.lean) | the plan's decoding table |
| [`claude_independent_review/lean_formal/tools/plan_k4_reordered.txt`](claude_independent_review/lean_formal/tools/plan_k4_reordered.txt) | the plan in plain text, codes reordered within each class |
| [`claude_independent_review/out/their_plan_k4_FINAL.txt`](claude_independent_review/out/their_plan_k4_FINAL.txt) | the plan in plain text, original order |
| [`claude_independent_review/out/their_plan_critical_codes.txt`](claude_independent_review/out/their_plan_critical_codes.txt) | an analysis of the plan's codes |

## 4. Software and references

- **Lean 4** and **elan** are developed by the Lean FRO and released under the Apache License 2.0. They are not redistributed here; the project pins the toolchain version in [`lean-toolchain`](claude_independent_review/lean_formal/lean_project/lean-toolchain).
- **Literature.** All literature used is cited in the [paper](claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md)'s reference list.
