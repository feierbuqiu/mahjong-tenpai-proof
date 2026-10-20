# Provenance

This page records where each part of the repository came from. Licence terms are in [`NOTICE.md`](../NOTICE.md).

## The puzzle: Lingzhi Shenpanzhe (零之审判者)

The puzzle was first posed by Lingzhi Shenpanzhe (Bilibili user 零之审判者) in a Bilibili post: <https://www.bilibili.com/opus/1246853448736964611>.

## The problem statement: feierbuqiu

| File | What it is |
|---|---|
| [`docs/呆饼问题（二）：听牌信息的排列编码问题.md`](呆饼问题（二）：听牌信息的排列编码问题.md) | feierbuqiu's Chinese original (research version of 19 October 2026) |
| [`docs/problem-statement.md`](problem-statement.md) | its English translation |

The original fixes the definitions, defines the two viewing models (adaptive and pre-fixed positions) and proves them equivalent. As written, it does not claim the value of *k*\*.

**Formula syntax.** The original wrote its formulas with the delimiters `\(…\)` and `\[…\]`, which GitHub does not display as mathematics. For publication here they were converted to GitHub's math syntax, and `\operatorname{Perm}`, which GitHub's math renderer does not allow, was written as `\mathrm{Perm}`. The text is otherwise unchanged.

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
| Generators and planners | [`lean_formal/tools/`](../claude_independent_review/lean_formal/tools/) | |
| Build evidence | [`lean_formal/logs/`](../claude_independent_review/lean_formal/logs/) | |
| Independent cross-check | [`src/`](../claude_independent_review/src/) (programs), [`out/`](../claude_independent_review/out/) (outputs) | Written from the problem statement, sharing no code with the original study. They re-derive the census (all 92,371,838 tenpai hands, 2,846 wait classes) and the lower-bound counts (7,875 / 5,628 / 347), and check both an independent plan (11,123 codes) and the original plan against every hand. |
| The paper | [`Four_Tiles_Suffice_Lean_Verification_Paper.md`](../claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md) | |

**Continuous integration.** The workflows in [`.github/workflows/`](../.github/workflows/) re-run the kernel check and the integrity checks on GitHub Actions; see [`reproducing.md`](reproducing.md).

**AI assistance.** This work was carried out with Anthropic's Claude Code running the Claude Opus 5.5 model. All proofs are checked by the Lean kernel.

**Independent review.** A separately operated AI agent reviewed the Lean sources statically. The paper (§5.5) lists its three findings, all of which were adopted.

## What was deliberately not published

| Material | Reason |
|---|---|
| internal working reports from earlier review rounds (in Chinese) | the paper summarises their conclusions |
| a Chinese-language version of the paper | not published, by choice |
| logs containing machine-specific paths, and compiled binaries | the programs' source code is included instead |
