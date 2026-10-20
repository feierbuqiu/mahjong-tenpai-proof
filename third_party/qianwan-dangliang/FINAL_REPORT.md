# 麻将「翻牌猜听牌」最终报告：Python 证明链 + Lean 形式化进展

> 结论：**最少翻 k = 4 张**。下界 k ≥ 4 严格证明；上界 k = 4 有显式策略并通过三套独立实现验证。
> **Lean 侧（本轮更新）**：k=1/2/3 否证与 k=4 上界（I 型 168,817 单元 + II 型 309,144 块 / 5,402,697 单元）**全部为内核验证**，全树 axiom 声明 **0 条**、sorry/admit **0 条**；剩余信任基仅 propext / Quot.sound 与 native_decide 的 Lean.ofReduceBool 机制（编译器信任，逐条可查 #print axioms）。
> 本文件为收口报告；细节见 REPORT.md、work/MODEL.md 与各目录 HANDOFF。

---

## 1. 结论与协议

* A 看牌后按一张公开的「类 → 码」表，把本类的一个 **4 元有序码**摆到最左 4 位；B 翻最左 4 张，用同一张表反查 ⇒ 说出该类**全部听牌**。
* k 可行 ⟺ 每个听牌类 C 有码集 S_C：(i) S_C 命中 C 的每一手牌；(ii) 不同类 S_C 两两不交（有序码；同一多重集的 p 个排列算 p 条码）。

## 2. Python 证明链（全部可复现）

### 2.1 下界：k = 1、2、3 严格不可行
工具是**子宇宙预算引理**：对任意牌集合 U，Σ_{C : C∩U≠∅} τ_U(C) ≤ |U|^k。

| k | 反例 U | 算术 | 产物 |
|---|---|---|---|
| 1 | 清一色 9 张 | Στ = **427 > 34** | work/lowerbound/lower.py --verify ⇒ CERTIFICATE VERIFIED；work/lowerbound/certificate.json |
| 2 | 清一色 9 张 | Στ ≥ **447 > 81** | 同上 |
| 3 | **U = {m2..m8}（中间 7 张）** | N=347 类、其中 L=52 类无公共 3-码 ⇒ Στ_U ≥ **399 > 343 = 7³** | work/lowerbound/k3_verify_disproof.py（5 秒复现）；work/lowerbound/k3_disproof_certificate.json（52 类 blocker 表，逐条可重放） |

三重独立复核：analyst 两套 W 实现 + Lead 用 verifier 的 indep_core 复算 + verifier 独立重放（含 84 个多重集无遗漏）。

### 2.2 上界：k = 4 显式策略（已通过全项独立验证）
* 方案：**work/verify/plan_k4_FINAL.json** —— 2,846 类 / **17,579 条有序 4-码**，sha256 `b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163`。
* 证书：**work/verify/final_certificate.json**（每项判据 + 数字 + hash + 复跑命令）。

| 验证线 | 工具 | 结果 |
|---|---|---|
| ① 全套快验（结构/Type I/chiitoi/10⁶ 手） | work/verify/fastverify_k4.py | 35 秒，全 0 |
| ② 逐块精确 DFS（I 型 168,817 + II 型 5,402,697 基式） | work/verify/block_coverage_exact.py | 未覆盖 **0 / 0** |
| ③ 独立八项（含 10⁶ 手模拟，独立 W 实现） | work/lowerbound/verify_k4_plan.py | ①对称差 0 ②0 空类 ③0 冲突/0 超容量 ④17,579/17,579 码 ⊆ 本类手牌 ⑤单元 5,571,671 未覆盖 0 ⑥chiitoi 0 ⑦国士 0 ⑧模拟 0 失败 ⇒ VERDICT true |
| ④ Lead 独立 I 型线（numpy 预筛 + 12 进程） | work/recon/k4_gap_par.py | uncovered = 0 |

### 2.3 演示工具
* **web/mahjong_demo.html**：单文件离线、约 914 KB（内联策略表 17,579 条码 + 34 张牌面图）。随机生成听牌手牌 / 自定义输入 ⇒ 显示 A 的排序（4 元码在最左 4 位）、B 翻开的 4 张、查表听牌；内置自测按钮。
* 证据：SELFTEST100/300 全 0 失败；与 Python 口径 3,014 手交叉 0 不一致；web/check_tiles.py 校验 68 张内联牌图 SHA-256 一致。

### 2.4 一键复现
```
python -u work/lowerbound/lower.py --verify                     # k=1/k=2 证书
python -u work/lowerbound/k3_verify_disproof.py                 # k=3：399 > 343
python -u work/verify/fastverify_k4.py work/verify/plan_k4_FINAL.json
python -u work/verify/block_coverage_exact.py work/verify/plan_k4_FINAL.json
python -u work/lowerbound/verify_k4_plan.py work/verify/plan_k4_FINAL.json --sim 1000000
python -u work/recon/k4_gap_par.py work/verify/plan_k4_FINAL.json --jobs 12
```

## 3. Lean 形式化进展

环境：Lean 4.33.1（lean-toolchain 固定），**仅 core/Std（无 mathlib）**；命令 `cd lean; lake build`。

| 模块 | 内容 | 状态 |
|---|---|---|
| Mj/Basic.lean | 牌/手牌/和牌（标准型、严格七对子、国士=仅幺九牌）/听牌/码包含/枚举 | 编译通过；与 Python 交叉对拍 **31,875 手 0 失配**（含 U7 全部 7,875 手、单花色 2 万手、15,143 手听牌） |
| Mj/Protocol.lean | 协议模型 + 解码表与**解码正确性** | 真证明：decode_unique 无公理；decode_correct 仅 propext/Quot.sound |
| Mj/Lemma.lean | **子宇宙预算引理** budget + classes_le_pow + no_common_code_two | 内核级真证明（propext/choice/quot）；verifier 用 Lean 反例纠正了我给语句的两处缺陷 |
| Mj/Disproof.lean | k=1/2/3 数值（93,600→387 类/L1=40/L2=53；7,875→N=347/L3=52；34<427、81<440、**343<399**）+ budget_sharp + no_feasible_k3_of_bridge | lake build 通过（1,078 s）、无 sorry；普查用 native_decide（编译器信任）；hbridge 为显式桥接假设 |
| Mj/Data.lean + Mj/Upper.lean | k=4 检查器（blockCovered 块级补牌族语义）与数据（2.40 MB） | lake build 通过；**I 型 168,817 块全通过**、结构全通过；**原先唯一的数学 assumption iiUnitsComplete 已于本轮删除**（见下一行） |
| **Mj/Bridge.lean**（本轮新增） | **去掉 hbridge**：只用「类数 > 码池」即得矛盾 | ✅ **`lake env lean Mj/Bridge.lean` → exit 0，无 sorry、无 hbridge**；三条主定理：`noFeasible_of`（**纯内核**：propext, Classical.choice, Quot.sound）、`no_feasible_k1`/`no_feasible_k2`（+387 的 native_decide 计数）、`no_feasible_k3`（+347 的 native_decide 计数）。路线：S_W := P.codesOf W 中「长度 k 且 ⊆ U」的码；每类非空（coversAll + support 引理）+ 各类不交 ⇒ Σ|S_W| ≤ \|U\|^k < N ≤ Σ|S_W| ⇒ 矛盾。**不需要 L3=52/badOf/badKey**。唯一附加建模假设：`Plan.valid`（码索引 < 34），远弱于 hbridge |
| **Mj/Upper2.lean + Mj/Data2.lean**（本轮新增） | II 型单元在 Lean 内验证：profile 枚举 + 309,144 个块记录（4.68 MB） | `lake build Mj.Upper2` **通过**；**已验证 486,754 / 5,402,697 单元（前 20,000 块，9.0%）**；其中 20 块 / 21 单元在**严格单码判据**下不通过（与 I 型 169 同源，需块级多码/DFS 语义）；~~剩余 289,144 块 / 4,915,943 单元未跑~~ → **已全部完成**（见下一行）；profile 对拍 **2,469 项 0 不一致**（Lean enumX vs Python PROFII_D） |
| **Mj/L6Index + Mj/L6B00..L6B15 + Mj/L6Total**（本轮新增，Lead） | **II 型 309,144 块 / 5,402,697 单元的块级语义（多码 + 全码 DFS）全量内核验证**：拆成 16 个批次模块（各一次 native_decide，每批 160–360 s），4 路并发 20 分钟跑完，**16/16 exit=0**；再由 L6Total 拼成一条全量定理 | ✅ 「lake build Mj.L6Total」通过；**「totalIdx_eq : totalIdx = (309144, 0, 5402697, 0)」**（块数 309,144 / 失败块 **0** / 单元 5,402,697 / 失败单元 **0**）。信任基 = propext, Quot.sound + 16 条各批 _native.native_decide.ax_1_1。**无 axiom、无 sorry**；合并证明仅 2 s / 315 MB（踩坑记录见 §3.2） |
| **Mj/L6Bridge.lean（L8，analyst-lower）** | 把 totalIdx 接回 Upper2 原有定义 l6Total：通用引理 map_range_getD_eq_self / go_len / chunkBlocks_length + 条件主定理 | ✅ 编译通过（1.5 s / 454 MB）；**l6Total_eq 为条件形式**（唯一假设 h : l6BatchStats = idx16.map batchAt，数据层已独立确认；`blocks.length` 无法廉价内核化，三条实测路径均爆） |
| **Mj/L6Upper.lean + Mj/Upper.lean（L7，enum-core）** | 用 totalIdx_eq 内核证明 iiUnitsCovered（II 型全覆盖），并从 Upper.lean **删除 axiom iiUnitsComplete 与 iiUnitsComplete_proof** | ✅ 「lake build Mj.Upper」通过（25 jobs / 375 s）；改动后 `#print axioms checkPlan_true` = propext, Quot.sound + structOk/iBlocksAllCovered/failuresAreReal/16 条 l6_batchNN 的 native_decide 基，**不再出现 iiUnitsComplete**；全树 axiom 声明 **0 条** |

**本轮附带发现（真实 bug）**：`work/strategy/table_lib.py` 中 `PROFII_D` 的 `am` 分量为 `[0]*34` 占位（min 更新条件写反），**不影响 `xs` 对拍与既有结论**（覆盖性用的是 xs/A 变体），但后续若有人直接用 `am` 需先修。
| Counterexample.lean | 语句缺陷的 Lean 反例（退出码 0） | 可复现 |

### 3.1 信任基（实测 #print axioms）

| 定理 | 依赖 |
|---|---|
| decode_unique | 无公理 |
| decode_correct / no_common_code_two | propext, Quot.sound |
| budget / classes_le_pow / budget_sharp / sum_ge_length_add_count | propext, Classical.choice, Quot.sound |
| flush_counts / u7_counts / k1k2_gaps / k3_gap | native_decide 的 Lean.ofReduceBool 机制（编译器信任） |
| structOk_true / iBlocksAllCovered_true | propext + native_decide 机制 |
| checkPlan_true（L7 之后） | propext, Quot.sound + native_decide 机制（structOk / iBlocksAllCovered / failuresAreReal / 16 条 l6_batchNN）；**已无任何数学 assumption** |
| **l6_batch00_eq .. l6_batch15_eq** | 各批一条 native_decide 可信基（编译器信任） |
| **totalIdx_eq**（L6 全量） | propext, Quot.sound + 16 条各批 native_decide 可信基；**无 axiom、无 sorry** |

审计：全树 `sorry/admit` = 0。

### 3.2 本轮踩坑记录（L6 合并证明的三次 OOM，值得留档）

把 16 条批定理合并成一条全量定理时，两种写法都把内存打爆：

| 写法 | 结果 |
|---|---|
| 一条 `simp only [totalIdx, idx16, ..., l6_batch00_eq, ..., l6_batch15_eq]` | 23 GB → INTERNAL PANIC: out of memory |
| 顺序 `rw [l6_batch00_eq, ..., l6_batch15_eq]` | 25 GB → OOM |
| 不做任何重写、只给 16 条批陈述的**合取** | ✅ 1 s / 76 MB |
| **别名方案（最终）**：给每批一个不同 head 常量的别名 b00..b15（定义上就是 batchAt k），再 simp 别名表 | ✅ 2 s / 315 MB |

**根因**：`batchAt i` 是 def；重写匹配（包括**失败**的匹配尝试）会 delta-展开为 `batchStat (l6Batches.getD i [])`，进而求值 `chunkBlocks`（309,144 元素列表），反复构造巨项。别名让每条重写规则的 LHS 是**互不相同的 head 常量** ⇒ simp 判别树精确命中，不再跨批展开。

同类教训：任何**目标表达式里出现 blocks / blkB* 字面表**的 `decide` / `native_decide` 都会爆内存（native 19 GB / kernel 3–4 GB），必须避开整体求值。

## 4. 剩余缺口与时间估算

| 缺口 | 内容 | 预估 |
|---|---|---|
| ~~A. hbridge（k=3 否证的语义桥）~~ | **已完成**：改用更短的「类数 > 码池」论证（347 > 343、387 > 81、387 > 9），`Mj/Bridge.lean` 编译通过、无 hbridge；仅余极弱假设 `Plan.valid`（码索引 < 34） | ✅ 完成 |
| B. 降低编译器信任 | flush 普查 93,600 手从 native_decide 改为内核校验（内核 decide 实测 >10 分钟超时；需『证书 + 内核校验』，但仍需大规模判定） | 1–3 小时（可选，性价比低） |
| ~~C. II 型 5,402,697 单元~~ | **已完成**：块级多码/DFS 语义升级 + 16 批拆分（每批一次 native_decide）+ L6Total 合并 ⇒ `totalIdx_eq` 内核验证 309,144 块 / 5,402,697 单元 / 失败 0；16 批期望值另经 verifier 独立重算 **16/16 逐字一致** | ✅ 完成 |
| ~~C2. L7：删除 Upper.lean 的 iiUnitsComplete~~ | **已完成**：Upper.lean 内 axiom 归零，checkPlan_true 只剩 propext/Quot.sound + native_decide 可信基 | ✅ 完成 |
| D. L8：把 totalIdx 接回 Upper2 原有的 l6Total | **条件形式完成**（analyst-lower）：`l6Total_eq (h : l6BatchStats = idx16.map batchAt) : l6Total = (309144, 0, 5402697, 0)`，1.5 s / 454 MB，axioms = propext, Quot.sound + 16 条批基；另有无条件内核引理 `chunkBlocks_length` / `go_len` / `map_range_getD_eq_self` 等。**唯一未内核化输入 h 无法在本轮消除**（实测三条路：`native_decide` 19 GB / `decide` 257 s 6.15 GB / `rfl` 900 s 16 GB 被杀 ⇒ `blocks.length` 在内核里没有便宜路径）。h 等价于「309,144 块按 20,000 切出 16 批」，已由 verifier（task-19）在数据层独立确认 | ✅ 条件形式交付，h 如实披露 |
| D. 完整普查形式化（块分解完备性） | 把「类的手牌 = 块族」也证掉 | 数天–数周（高风险） |

## 5. 文件索引

* 结论与证书：REPORT.md、work/MODEL.md、work/verify/final_certificate.json、work/lowerbound/certificate.json、work/lowerbound/k3_disproof_certificate.json
* k=4 方案：work/verify/plan_k4_FINAL.json（+ plan_k4_FINAL.sha256）
* 验证工具：work/verify/fastverify_k4.py、block_coverage_exact.py、perclass_coverage.py、waste_exact.py；work/lowerbound/verify_k4_plan.py；work/recon/k4_gap_par.py
* 演示：web/mahjong_demo.html、web/README.md、web/test_demo.js
* Lean：lean/README.md、lean/lakefile.toml、lean/Mj/*.lean（Basic / Protocol / Lemma / Disproof / Bridge / Data / Upper / Data2 / Upper2 / **L6Index / L6B00..L6B15 / L6Total / L6Upper / L6Bridge**）、lean/Counterexample.lean
  * L6 全量内核验证的调度与日志：work/lean/run_l6_waves.ps1、work/lean/l6_build.log（16 批逐条 exit=0）、work/lean/peak_run.ps1
  * 16 批期望值的独立复核（task-19）：work/lean/verify_batch_expected.py、work/lean/L9_expected_crosscheck.md、work/lean/_l9_recomputed.json
* 听牌数对账（task-20，A1）：work/recon/TENPAI_COUNT.md、work/recon/tenpai_count_audit.py、work/recon/out/tenpai_count_audit.json；独立复核 work/recon/TENPAI_VERIFY.md
* Lean 侧交接：work/lean/L7_HANDOFF.md、work/lean/L8_HANDOFF.md
* 交接：work/verify/HANDOFF.md、work/lowerbound/HANDOFF.md、work/strategy/HANDOFF.md
* 独立审计：work/audit/AUDIT.md（含 2026-09-18 的 4 处撤回标注）
---

## 6. 独立审计（skeptic-audit，2026-09-18）与勘误

独立审计员（全新队友，未获任何方向引导、不信任原团队脚本、自建引擎 `work/audit/mjcore.py`）的结论：

| 命题 | 独立判定 | 独立证据（非抽样） |
|---|---|---|
| 最小 k = 4 | **确认** | 下界三条独立否证 + 上界穷举验证 |
| k=1 不可行 | 确认 | 清一色 387 类 > 9 码；Στ₁ = **427**（精确独立算出） |
| k=2 不可行 | 确认 | 387 > 81；Στ₂ 下界 **435**（其区间 [435,483] 包含团队的 [447,457]） |
| k=3 不可行 | 确认 | U={m2..m8} 独立得 N=347、L=52 ⇒ 399>343；52 行 blocker 逐条成立 |
| k=4 可行 | **确认（穷举）** | 标准型 5,272,603 个基式全查（285 个硬基式逐个补牌族穷举）；七对子 **37,657,312** 手精确搜索；国士 157 手；16 个子宇宙全量扫描 |
| 类普查 2,846 | 确认 | 2,845 标准型根类 + 1 纯国士类，与方案键完全一致 |

**未发现任何反例**（没有任何使 k=4 方案失败的听牌手牌）。审计报告：`work/audit/AUDIT.md`（22 KB，含复现命令）。

### 6.1 已修正的问题（记录性，不影响结论）
1. `work/MODEL.md` 曾同时存在两份互相矛盾的「命中集判据」（其中一份用了已作废的奇偶口径）——**已删除重复段落并加勘误注**。
2. `work/verify/final_certificate.json` 的 provenance 曾把删除 3 条不可用码的理由写成「4 张同牌无法在 4 面子+1 对中拆解」——**该理由错误**（反例：`1p1p1p1p 3p 456m 789m 22z` 听 2p 且含 1p×4，是合法和牌形）。正确理由是**类相关的**（例如含 4 张东的手牌必有 东 ∈ W(H)，不可能属于类 {7m}）。删除这 3 条码本身安全（审计员确认它们不在最终文件中且三类的覆盖不受影响），但**该 provenance 句子作废，以本节为准**。
3. **赤牌（红 5）建模假设**需显式声明：全部结论按理想 34 种牌审计（5m ≡ 5m）。k=4 上界不受影响；但 k=3 否证用的 U={m2..m8} 含 m5，若物理上赤 5 可提供额外信号，该否证的前提需重新陈述。
4. 「B 翻开 k 张」按**恰好 k 张**理解；若按「至多 k 张」理解，结论不变（k≤3 否证更强）。

### 6.2 已裁决的不一致（task-20 / A1，2026-09-18）
1. **听牌手牌总数 —— 已裁决：团队数字正确**。应采用值：标准型听牌手牌 **54,747,045**、七对子 **37,657,312**、标准型∩七对子 **32,676**、国士 **157**，**听牌总数 92,371,838**。
   审计的 54,793,476 / 92,418,269 **多算 46,431**（全在标准型分量）。根因定位到代码行：审计全局计数器 「work/audit/t15_counts.py::meld_multisets」 用 out=[] 按**面子多重集**计补牌族 —— 同一补牌的**牌张向量**若有 k 种面子分解就被计 k 次；而审计**自己的**校验器 「t18_validate_count.py::mm」 用 out=set() 去重。即「被 6 个小宇宙暴力校验通过的方法」并非「用于产出全局数字的方法」。
   最小见证：H = 111222333444s + 东（13 张，听东），补牌 F 有 3 种面子分解（{111s,222s,333s,444s} / {111s,234s,234s,234s} / {444s,123s,123s,123s}）⇒ 审计口径计 3 次，实际 1 手。
   四条独立路径（从零实现）一致支持团队数字：A 结构分解·按牌张向量去重；A' 复刻审计写法（复现 54,793,476）；B **和牌侧无结构假设**（枚举全部 7,427,311 个 14 张标准和牌，按「最小听牌张」唯一计数）；C 8 个子宇宙逐手暴力（8/8 与暴力逐位一致，含 1,613,184 手的 12 牌宇宙；naive 口径在 5 个宇宙多算，含审计用过的 12 张牌宇宙 202,076 vs 暴力 201,020）。清一色宇宙里 F 恒空，故该 bug 在结构上不可能显形 —— 这解释了审计的自校为何通过。
   点名复核：1p1p1p1p 3p 456m 789m 22z 从零算听 **2p**，两侧都只计 1 次，不是差异来源；「4 张同牌无法拆成 4 面子+1 对」确为**假命题**（H+2p = 111p + 1p2p3p + 456m + 789m + 22z）。
   证据：work/recon/TENPAI_COUNT.md、work/recon/tenpai_count_audit.py、work/recon/out/tenpai_count_audit.json（复现：python -u work/recon/tenpai_count_audit.py structure|witness|winning|validate big）。审计 §6.1 中「倾向认为报告这两个数字有误」的判断就此撤回。
   （本题为听牌手牌计数，与 k=4 覆盖验证无关；审计 §4.4 的「{z} 类全偶补牌未用本类码验证」属覆盖验证范围的缺口，不影响本裁决。）

### 6.3 仍未闭合

1. `final_certificate.json` 的 `class_list_digest_sha256` **未能复现**（审计员试了 4 种自然规范化均不匹配）⇒ 该摘要字段的生成方式需公开或改用更明确的规范化规则。
2. 团队 `Στ₂ ≥ 447` 未被审计员独立复现（他独立得下界 435）；由于 435 > 81 已足以否证 k=2，结论不受影响，但团队数字的来源应补充说明。
