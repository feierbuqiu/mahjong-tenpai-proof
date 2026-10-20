# 麻将「翻牌猜听牌」证明成果包（两条路径汇总）

* 生成时间：2026-09-18（本会话末）
* 结论：**最少翻 k = 4 张**。k = 1、2、3 严格不可行；k = 4 有显式策略并被穷举验证。
* 本包包含两条独立证明路径：
  * **路径 A（Python 证明链）**：数值构造 + 证书 + 三套独立实现 + 全新队友的独立审计（穷举，0 反例）。
  * **路径 B（Lean 4 形式化）**：k=1/2/3 否证与 k=4 上界的核心部分为内核验证，**全树 axiom 声明 0 条、sorry/admit 0 条**。

---

## 0. 一句话结论与协议

* A 看 13 张关门听牌手牌，按公开的「类 → 码」表把本类的一个 **4 元有序码**摆到最左 4 位（其余任意排列）；
  B 只需翻最左 4 张，用同一张表反查，即可说出该类**全部**听牌。
* 可行性等价条件：存在码集分配 S_C（C 遍历全部听牌类），满足
  (i) **覆盖**：S_C 中每条码都 ⊆ 该类的每一手牌（c ⊆ H）；
  (ii) **不交**：不同类的 S_C 两两不交（同一多重集的 p 个排列算 p 条有序码，权重 p₄(μ) = 24/∏mult!）。
* k 可行 ⟺ k-1 不可行即证下界；给出满足 (i)(ii) 的显式方案即证上界。

---

## 1. 路径 A：Python 证明链

### 1.1 下界（k = 1、2、3 全部不可行）

| k | 反例构造 | 不等式 | 证书 |
|---|---|---|---|
| 1 | 清一色 387 个类 | Στ₁ = **427 > 9** | work/lowerbound/certificate.json |
| 2 | 清一色 387 个类 | Στ₂ ≥ **447 > 81**（审计独立得下界 435，同样 > 81） | 同上 |
| 3 | U = {m2..m8}（7,875 手 / 347 类） | N = 347、L = 52 ⇒ **399 > 343 = 7³** | work/lowerbound/k3_disproof_certificate.json |

关键引理（**子宇宙预算引理**）：对任意牌集 U，Σ_{C: C∩U≠∅} τ_U(C) ≤ |U|^k；
即「每个类至少要一条完全落在 U 内的码，且这些码两两不交」。k=3 的否证只需 N > |U|³，不依赖精细的 L 值。

### 1.2 上界（k = 4 的显式方案）

* 方案：**2,846 个类 / 17,579 条有序 4-码**，文件 work/verify/plan_k4_FINAL.json，
  sha256 = b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163。
* 结构自检（全部内核/Python 双查）：类键唯一、有序码全局唯一（⇒ 各类码集不交）、无空类、码索引合法。

验证工具与结果：

| 工具 | 内容 | 结果 |
|---|---|---|
| work/verify/fastverify_k4.py | 全方案结构 + 类型抽查 | 35 s 通过 |
| work/verify/block_coverage_exact.py | **块级语义**全覆盖：I 型 168,817 + II 型 5,402,697 基式 | **0 未覆盖 / 0 失败**（II 型 8 进程 93.9 s） |
| work/lowerbound/verify_k4_plan.py | 8 项检查 + 10⁶ 随机手牌 | 0 失败 |
| work/recon/k4_gap_par.py | Lead 独立实现交叉核对 | 0 失败 |
| work/audit/*（skeptic-audit） | **独立引擎 + 穷举 23,208,594 手 / 1,832,404 听牌**（16 个牌集全枚举、标准型 5,272,603 基式、七对 37,657,312 手精确搜索、国士 157 手） | **0 反例**，类普查互相包含 |

### 1.3 听牌手牌计数（本轮裁决）

采用值（三条独立路径一致）：标准型听牌手牌 **54,747,045**、七对子 **37,657,312**、标准型∩七对子 **32,676**、国士 **157**、**听牌总数 92,371,838**。

* 独立审计一度算出 54,793,476 / 92,418,269（多算 46,431），本轮定位到具体代码行并撤回：
  审计的 work/audit/t15_counts.py::meld_multisets 用 out=[] 按**面子多重集**计数（同一补牌牌张向量有 k 种分解就计 k 次），
  而它**自己的**校验器 t18_validate_count.py::mm 用 out=set() 去重 ⇒「被小宇宙暴力校验通过的方法」并非「产出全局数字的方法」。
* 最小见证：H = 111222333444s + 东（听东），补牌 F 有 3 种面子分解 ⇒ 审计口径计 3 次、实际 1 手。
* 双重独立确认：task-20（designer-encoder，四条路径）+ verifier 独立复核（自写实现、两法 + 静态口径证据、top-10 多算量逐项吻合）。

### 1.4 勘误（记录性，不影响结论）

1. work/MODEL.md 曾有两份矛盾的「命中集判据」（其一为已作废的奇偶口径）→ 已删除重复段并加勘误。
2. final_certificate.json 的 provenance 曾把「删除 3 条不可用码」的理由写成「4 张同牌无法拆成 4 面子+1 对」——**该理由为假**
   （反例：1p1p1p1p 3p 456m 789m 22z 听 2p）。正确理由与类相关；删除本身安全。
3. **赤牌（红 5）建模假设**：全部结论按理想 34 种牌；k=3 否证用的 U 含 m5，若赤 5 提供额外信号需重述该前提。
4. 「B 翻开 k 张」按**恰好 k 张**理解；按「至多 k 张」结论不变。

---

## 2. 路径 B：Lean 4 形式化

环境：Lean 4.33.1（lean-toolchain 固定），主项目 **仅 core/Std**（无 mathlib）；命令 cd lean && lake build。
默认构建 **32 jobs / exit 0**；全树 **axiom 声明 0 条**、sorry/admit 0 条。

### 2.1 模块与内容

| 模块 | 内容 | 状态 |
|---|---|---|
| Mj/Basic.lean | 牌/手牌/和牌（标准型、严格七对子、国士=仅幺九）/听牌/码包含/枚举 | 通过；与 Python 交叉对拍 **31,875 手 0 失配** |
| Mj/Protocol.lean | 协议模型 + 解码表与解码正确性 | decode_unique 无公理；decode_correct 仅 propext/Quot.sound |
| Mj/Lemma.lean | **子宇宙预算引理** budget + classes_le_pow + no_common_code_two | 内核真证明 |
| Mj/Disproof.lean | k=1/2/3 数值（93,600→387 类 / 40,196 / 387 / 40；7,875→N=347 / L=52；34<427、81<440、**343<399**） | 通过，native_decide 普查 |
| Mj/Bridge.lean | **去掉 hbridge** 的语义桥：类数 > 码池即矛盾 | no_feasible_1/2/3 通过；唯一建模假设 Plan.valid（码索引 < 34） |
| Mj/Data.lean + Mj/Upper.lean | I 型块级检查器与数据 | **168,817 个 I 型单元全通过**；**原 axiom iiUnitsComplete 已删除** |
| Mj/Data2.lean + Mj/Upper2.lean | II 型：profile 枚举 + 309,144 条块记录（4.68 MB），块级多码/全码 DFS 语义 | 通过；profile 对拍 2,469 项 0 不一致 |
| **Mj/L6Index + L6B00..L6B15 + L6Total** | **II 型全量内核验证**：16 批各自 native_decide，再由别名方案合成一条定理 | 16/16 exit=0；**totalIdx_eq : totalIdx = (309144, 0, 5402697, 0)**（失败块 0 / 失败单元 0），2 s / 315 MB |
| Mj/L6Upper + Upper.lean（L7） | 用 totalIdx_eq 内核证明 iiUnitsCovered，并从 Upper.lean **删除 iiUnitsComplete** | checkPlan_true 不再含任何数学假设 |
| Mj/L6Bridge.lean（L8） | 通用引理 map_range_getD_eq_self / foldl_eq_of_fun_eq / go_len / chunkBlocks_length + 条件主定理 l6Total_eq | 编译通过（1.5 s / 454 MB） |

### 2.2 关键信任基（实测 #print axioms）

| 定理 | 依赖 |
|---|---|
| decode_unique | 无公理 |
| foldl_eq_of_fun_eq | 无公理 |
| budget / classes_le_pow / noFeasible_of | propext, Classical.choice, Quot.sound |
| no_feasible_k1 / k2 / k3 | 上述 + 对应普查的 native_decide 基 |
| structOk_true / iBlocksAllCovered_true | propext + 各自 native_decide 基 |
| **totalIdx_eq** | propext, Quot.sound + 16 条 l6_batchNN 的 native_decide 基 |
| **checkPlan_true（L7 后）** | propext, Quot.sound + structOk / iBlocksAllCovered / failuresAreReal + 16 条批基，**无 iiUnitsComplete** |
| l6Total_eq（L8，条件） | 同上 + 假设 h |

> 说明：native_decide 的可信基是 Lean 的 Lean.ofReduceBool 机制（编译器信任），逐条可用 #print axioms 复核；它不是数学假设。

### 2.3 L8 的条件形式与唯一未内核化输入

* 主定理（条件）：**l6Total_eq (h : l6BatchStats = idx16.map batchAt) : l6Total = (309144, 0, 5402697, 0)**。
* h 的内容等价于「309,144 条块记录按 20,000 一批恰好切出 16 批」，数据层已由 task-19 独立确认；
  但 **blocks.length = 309144 在 Lean 内核里没有便宜路径**（三条实测：native_decide 19 GB 未完成；
  内核 decide 257 s / 6.15 GB；内核 rfl 900 s / 16 GB 均未完成）⇒ 本轮无法消掉 h，已如实披露。

### 2.4 展开陷阱（本轮最重要的工程教训，已写入 §3.2 与 HANDOFF）

* 任何对 l6Batches / batchAt / l6BatchStats / chunkBlocks 的 rw/simp/rcases/rfl-defeq 匹配都会
  delta-展开成 chunkBlocks 20000 blocks → blocks.length，反复构造 309k 元素的巨项 ⇒ 3–25 GB 内存或 maxRecDepth。
* 合并 16 条批定理的两种「自然写法」（一条 simp only 带 16 条重写规则；顺序 rw 16 次）分别冲到 23 GB / 25 GB。
* **解法**：给每批一个 head 常量互不相同的别名 b00..b15（定义上就是 batchAt k），让 simp 判别树精确命中 ⇒ 2 s / 315 MB。

---

## 3. 外部独立确认（跨路径）

| 项目 | 独立方 | 结果 |
|---|---|---|
| Python 结论 k=4 | skeptic-audit（全新队友、自建引擎、不给方向） | 穷举 23,208,594 手 → 0 反例 |
| 16 批期望值（Lean 定理的陈述目标） | verifier（task-19） | **16/16 逐字一致**，合计 (309144, 0, 5402697, 0) |
| 听牌总数（54,747,045 / 92,371,838） | designer-encoder（四条路径）+ verifier（独立两法） | 双方一致；审计口径被定位并撤回 |
| Lean Basic 和牌/听牌判定 | 与 Python indep_core.compute_W 对拍 | 31,875 手 0 失配 |

---

## 4. 复现命令

**Python 路径**

    cd /d D:\DSH\MJ2
    python -u work/verify/fastverify_k4.py                  # 方案结构自检（35 s）
    python -u work/verify/block_coverage_exact.py           # I/II 型块级全覆盖（0 失败）
    python -u work/lowerbound/verify_k4_plan.py             # 8 项检查 + 10^6 手
    python -u work/recon/k4_gap_par.py                      # 独立交叉核对
    python -u work/recon/tenpai_count_audit.py structure    # 听牌数对账（另见 TENPAI_COUNT.md）
    python -u work/lean/verify_l6.py                        # II 型 5,402,697 单元独立复算
    python -u work/lean/verify_batch_expected.py            # 16 批期望值独立重算（task-19）

**Lean 路径**

    cd /d D:\DSH\MJ2\lean
    lake build                                              # 全部默认目标（32 jobs）
    lake env lean Mj/L6Total.lean                           # 查看 totalIdx_eq 的 #print axioms

（mathlib 环境在 lean-mathlib/，本包只含其 lakefile/lake-manifest/lean-toolchain 配置，不含 6.7 GB 依赖缓存。）

---

## 5. 未闭合项（如实列出）

1. **L8 的 h**（见 §2.3）——唯一未内核化输入，已由数据层独立确认。
2. final_certificate.json 的 class_list_digest_sha256 未能复现（4 种规范化都不匹配）⇒ 生成方式需公开或改用更明确的规则。
3. 团队 Στ₂ ≥ 447 未被审计独立复现（审计得 435，> 81 已足够否证 k=2）⇒ 来源需补充说明。
4. 「类的完备性」（手牌 = 块族的分解定理）在 Lean 中未形式化；Python 侧由小宇宙暴力校验 + 审计穷举支撑。
5. 赤牌口径为建模假设（§1.4 第 3 条）。

---

## 6. 包内索引

* 报告：FINAL_REPORT.md（收口报告）、REPORT.md、PROOF_SUMMARY.md（本文件）、mahjong-question2.md（原始问题）
* Python 下界：work/lowerbound/（证书、普查脚本、HANDOFF）
* Python 上界与验证：work/verify/（plan_k4_FINAL.json、final_certificate.json、各验证脚本）、work/strategy/（方案生成器与类表）、work/recon/（独立对账、听牌数对账）
* 独立审计：work/audit/（AUDIT.md + 20 个自建脚本，含 4 处撤回标注）
* Lean：lean/（lakefile.toml、toolchain、Mj/*.lean 全部模块含数据、Counterexample.lean）
* Lean 交接：work/lean/（L7_HANDOFF.md、L8_HANDOFF.md、L9_expected_crosscheck.md、verify_l6.py 等）
* 演示：web/mahjong_demo.html（单文件离线，随机/自定义手牌 → 排序 + 翻牌 + 听牌）
* 打包脚本：work/make_package.ps1

> 排除项（可再生/体积过大）：lean/.lake 构建产物、lean-mathlib 依赖缓存、*.pkl 缓存、__pycache__、
> 中间搜索产物（work/strategy/out/replace_candidates.json、各轮 plan_k4_v*/u* 变体）、内存测量残留。
