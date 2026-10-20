# Provenance

This page records where each part of the repository came from. Licence terms are in [`NOTICE.md`](../NOTICE.md).

## The puzzle: Lingzhi Shenpanzhe (零之审判者)

The puzzle was first posed by Lingzhi Shenpanzhe (Bilibili user 零之审判者) in a Bilibili post: <https://www.bilibili.com/opus/1246853448736964611>. The paper (Section 1.1) defines it precisely, including the combinatorial form that the Lean specification transcribes.

## The computation and the construction: Qianwan Dangliang (千万当量)

Qianwan Dangliang's study is in [`third_party/qianwan-dangliang/`](../third_party/qianwan-dangliang/). It was posted in reply to Lingzhi Shenpanzhe's Bilibili post and shared on Baidu Netdisk (<https://pan.baidu.com/s/1qdCW0N75TZzIRsUYx-75Tw?pwd=utfx>). The study established *k*\* = 4. It produced:
- the census;
- the lower-bound argument;
- the encoding plan [`work/verify/plan_k4_final.json`](../third_party/qianwan-dangliang/work/verify/plan_k4_final.json) (2,846 classes, 17,579 ordered codes, SHA-256 `b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163`, matching the hash distributed with it).

**The mirror.** It is byte-for-byte as received, except that one Python bytecode cache directory is omitted; see [`third_party/README.md`](../third_party/README.md). Checksums of all 989 mirrored files are in [`third_party/qianwan-dangliang.SHA256SUMS`](../third_party/qianwan-dangliang.SHA256SUMS).

## The formal proof and the independent cross-check: feierbuqiu, with AI assistance

These are in [`claude_independent_review/`](../claude_independent_review/).

| Part | Path | Notes |
|---|---|---|
| Lean 4 project | [`lean_formal/lean_project/`](../claude_independent_review/lean_formal/lean_project/) | The data modules `Tenpai/Data/ClassTree.lean` and `DecodeTree.lean` are generated from Qianwan Dangliang's plan, with codes reordered **within** each class only. Every class's code list is unchanged as a multiset. `Tenpai/Data/Witness.lean` is generated from `out/u7_certificate.txt`, our own independent computation. |
| Generators and planners | [`lean_formal/tools/`](../claude_independent_review/lean_formal/tools/) | [`check_regeneration.py`](../claude_independent_review/lean_formal/tools/check_regeneration.py) regenerates every generated file and confirms the plan's provenance. |
| Build evidence | [`lean_formal/logs/`](../claude_independent_review/lean_formal/logs/) | the local from-scratch build (`clean_build/`) and the online build (`ci_build/`) |
| Independent cross-check | [`src/`](../claude_independent_review/src/) (programs), [`out/`](../claude_independent_review/out/) (outputs) | Written from the problem's definitions, sharing no code with the original study. They re-derive the census (all 92,371,838 tenpai hands, 2,846 wait classes) and the lower-bound counts (7,875 / 5,628 / 347), and check both an independent plan (11,123 codes) and the original plan against every hand. [`src/recheck.sh`](../claude_independent_review/src/recheck.sh) re-runs them against the recorded outputs; [`out/recheck.log`](../claude_independent_review/out/recheck.log) is its local run. |
| The paper | [`Four_Tiles_Suffice_Lean_Verification_Paper.md`](../claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md) | |

**Continuous integration.** The workflows in [`.github/workflows/`](../.github/workflows/) re-run the kernel check, the integrity and regeneration checks and the cross-check on GitHub Actions, and run CodeQL code scanning; see [`reproducing.md`](reproducing.md).

**AI assistance.** This work was carried out with Anthropic's Claude Code running the Claude Opus 5.5 model. All proofs are checked by the Lean kernel.

**Independent reviews.** Two separately operated AI agents reviewed the work:
- a static review of the Lean sources, whose three findings were all adopted;
- an audit of the published repository at commit `0c786e3`, whose seven engineering findings were all addressed.

The paper (Section 5.5) lists both sets of findings and our responses. Neither found an error in the specification or the proof.

## Release

The state described in the paper is frozen as [release v1](https://github.com/feierbuqiu/mahjong-tenpai-proof/releases/tag/v1) (Git tag `v1`).

## What was deliberately not published

| Material | Reason |
|---|---|
| internal working reports from earlier review rounds, and the review reports themselves (in Chinese) | the paper summarises their conclusions and findings |
| a Chinese-language version of the paper | not published, by choice |
| logs containing machine-specific paths, and compiled binaries | the programs' source code is included instead |
