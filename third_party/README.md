# Third-Party Material

## `qianwan-dangliang/`: the original computational study

**Author:** Qianwan Dangliang (Bilibili user 千万当量).

**Where it was published:**
- posted in reply to the Bilibili puzzle <https://www.bilibili.com/opus/1246853448736964611>;
- shared on Baidu Netdisk: <https://pan.baidu.com/s/1qdCW0N75TZzIRsUYx-75Tw?pwd=utfx>.

**What it is.** The study that first established the answer *k*\* = 4:
- an exhaustive census of tenpai hands;
- the lower-bound argument on the sub-universe {2m, …, 8m} (347 wait sets against 7³ = 343 messages);
- the explicit four-tile encoding plan, with 2,846 classes and 17,579 ordered codes ([`work/verify/plan_k4_final.json`](qianwan-dangliang/work/verify/plan_k4_final.json), SHA-256 `b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163`);
- the author's Python verifiers, a web demonstration and a Lean development.

The repository's own formal proof ([`claude_independent_review/`](../claude_independent_review/)) uses this plan as an untrusted certificate and re-checks it in the Lean kernel. It does not modify the author's solution process or construction.

### Why it is mirrored here

The material was available only through a cloud-drive share. Mirroring it in a public repository gives it:
- a stable location;
- version history;
- checksums;
- clear attribution.

The mirror is **verbatim**:
- Every file is byte-for-byte as received, in its original language, mostly Chinese.
- The one exception is the Python bytecode cache `work/lowerbound/__pycache__/`, which was not included; the author's own packaging script ([`work/make_package.ps1`](qianwan-dangliang/work/make_package.ps1)) also excludes such caches.
- [`qianwan-dangliang.SHA256SUMS`](qianwan-dangliang.SHA256SUMS) lists the SHA-256 of all 989 mirrored files.
- Nothing was reformatted for GitHub, so the author's Markdown files are shown exactly as written.

To check the mirror, run from this directory:

```bash
sha256sum -c qianwan-dangliang.SHA256SUMS
```

### Terms

- **No licence was distributed with the package; all rights remain with its author.** The repository's MIT Licence does **not** apply to anything in `qianwan-dangliang/`.
- The scripts contain absolute paths from the author's own machine and were written for that environment.
- **Images of unknown origin.** According to the author's [`web/README.md`](qianwan-dangliang/web/README.md), the tile images in [`web/pai-images/`](qianwan-dangliang/web/pai-images/), also embedded in [`web/mahjong_demo.html`](qianwan-dangliang/web/mahjong_demo.html), were supplied to the author. Their original source and licence are not documented, and any rights in them remain with their owners.
- **Removal.** The author or any rights holder can ask for the mirror to be changed or removed by opening an issue.

### A guide to the package

| Path | Contents |
|---|---|
| [`FINAL_REPORT.md`](qianwan-dangliang/FINAL_REPORT.md), [`REPORT.md`](qianwan-dangliang/REPORT.md), [`PROOF_SUMMARY.md`](qianwan-dangliang/PROOF_SUMMARY.md) | The author's reports, in Chinese |
| [`mahjong-question2.md`](qianwan-dangliang/mahjong-question2.md) | The author's statement of the question |
| [`work/data/`](qianwan-dangliang/work/data/), [`work/strategy/`](qianwan-dangliang/work/strategy/), [`work/recon/`](qianwan-dangliang/work/recon/) | Census, block decomposition and construction programs |
| [`work/verify/`](qianwan-dangliang/work/verify/), [`work/lowerbound/`](qianwan-dangliang/work/lowerbound/), [`work/audit/`](qianwan-dangliang/work/audit/) | Verifiers, lower-bound programs and certificates, the author's internal audit |
| [`lean/`](qianwan-dangliang/lean/), [`lean-mathlib/`](qianwan-dangliang/lean-mathlib/) | The author's Lean development (Lean 4.33.1) |
| [`web/`](qianwan-dangliang/web/) | A browser demonstration of the encoding protocol |
