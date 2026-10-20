# lean-mathlib —— 独立的 mathlib 环境（与 `../lean` 的 core/Std 形式化并行、互不影响）

## 现状（已安装可用）
* 工具链：`leanprover/lean4:v4.33.1`（`lean-toolchain` 固定）
* mathlib：`v4.33.1`（与工具链同版本，`lakefile.toml` 里 `[[require]] name = "mathlib"`）
* 依赖齐备：aesop / batteries / Cli / importGraph / LeanSearchClient / mathlib / plausible / proofwidgets / Qq
* 预编译缓存已下载：`mathlib/.lake/build` 约 **6.2 GB**（`lake exe cache get` 的 8690 个文件）
* 冒烟验证：`lake build MjML` → **Build completed successfully (8707 jobs)**；`#eval Finset.card (Finset.univ : Finset (Fin 5))` = 5 ✓；`Finset.card_biUnion` 可用 ✓

## 安装过程中遇到的网络问题与解法（可复现）
1. 直连 GitHub 克隆 mathlib 中途 `RPC failed; curl 56 Recv failure: Connection was reset` ⇒ 改用镜像；
2. 主镜像 `gh-proxy.com` 对 `LeanSearchClient` 返回 `403 Web page content is not allowed` ⇒ 换备用镜像 `ghfast.top`；
3. git 全局 URL 重写（本机已设置）：
   ```
   git config --global url."https://ghfast.top/https://github.com/".insteadOf "https://github.com/"
   ```
   之后 `lake update`（拉齐 9 个依赖）+ 缓存下载一次成功。

## 使用
```
cd lean-mathlib
lake build MjML                     # 冒烟（已通过）
lake env lean 你的文件.lean          # 在 mathlib 环境下跑脚本/证明
```

## 与现有形式化的关系（重要）
* `../lean`（本项目的 Lean 形式化）**刻意只用 core/Std、不用 mathlib**，因此其信任基更小（`#print axioms` 里只有 propext / Classical.choice / Quot.sound 与 `native_decide` 机制），**不要**把它迁到 mathlib，以免引入 mathlib 的公理与依赖；
* mathlib 环境用于**新的/更省力的**开发，例如：
  * 用 `Finset.card_biUnion` 重写 `Mj.Lemma.budget`（原实现为手写 List 版本）；
  * `hbridge` 那类引理（集合/基数/不相交并）在 mathlib 下通常更短；
  * 若将来要把 II 型 5.4M 单元做成「证书 + 内核校验」，mathlib 的 `Finset`/`Fintype` 计数工具也更方便。
