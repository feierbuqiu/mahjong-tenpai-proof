# 交接报告 — analyst-lower（下界 / k=3 否证 / k=4 修复支援）

## 0. 一句话结论
**k = 1、2、3 均已严格否证 ⇒ 最小可行 k ≥ 4。** k=4 的显式策略（plan）尚差两处残余，见 §4。

## 1. 交付物与复现命令

| 文件 | 内容 |
|---|---|
| `work/lowerbound/certificate.json` | k=1..4 的 Στ 区间与逐类见证（`cover_codes` 上界见证 + `blockers` 下界见证） |
| `work/lowerbound/lower.py` | 可复现主脚本；`python -u work/lowerbound/lower.py --verify` → `CERTIFICATE VERIFIED` |
| `work/lowerbound/LOWERBOUND.md` | 引理 1–6 的证明、定理 A/B、§10 的 k=3 追加节 |
| `work/lowerbound/k3_disproof_certificate.json` | k=3 否证证书：347 个类的 W 全表 + sha256 + 52 个 L 类的 blocker 表 |
| `work/lowerbound/k3_verify_disproof.py` | 5 秒复现 k=3 否证（打印 399 > 343） |
| `work/lowerbound/k3_subuniverse.py` / `k3_merge.py` / `k3_summary.json` | 187 个 U 的普查与汇总 |
| `work/lowerbound/K3_DISPROOF.md` | k=3 否证的完整书面论证 |
| `work/strategy/out/`（k=4） | 见 `work/strategy/out/HANDOFF_v3.md` |

## 2. k=1 / k=2 否证（T3，已完成）

判据（子宇宙预算引理）：对牌集 U，Σ_{C : C∩U≠∅} τ_U(C) ≤ |U|^k。
取 U = {m1..m9}（清一色，387 个类，全部手牌落在 U 内）：

| k | Στ（清一色 387 类） | 预算 9^k | 结论 |
|---|---|---|---|
| 1 | **427**（精确：347 类 τ=1、40 类 τ=2） | 9 | 427 > 9（也 > 34）**不可行** |
| 2 | **≥ 447**（387 + 53 + 7） | 81 | 447 > 81 **不可行** |

复现：`python -u work/lowerbound/lower.py --verify`。
附：全局计数亦可否证 k=2（严格口径全局类数 2846 > 34²=1156）。

## 3. k=3 否证（T8，已完成）— U = {m2..m8}

**判据**：N(U) = 有"手牌全落在 U 内"的类数；L(U) = 其中在 U 内无公共 3-码的类数。
则 Στ_U ≥ N + L；而引理给出 Στ_U ≤ |U|³。**N + L > |U|³ ⇒ k=3 不可行。**

**否证 U = {m2,m3,m4,m5,m6,m7,m8}（7 张）**：

| 量 | 值 |
|---|---|
| 13 张 ⊆ U 的计数向量 | 7,875（完全枚举） |
| 听牌手牌 | 5,628 |
| **N(U)** | **347** |
| **L(U)** | **52** |
| 码池 \|U\|³ | **343** |
| **N + L** | **399 > 343** ⇒ 否证 |

**关键洞察（"中间 7 张"）**：不是"7 张"而是"哪 7 张"。{m1..m7} 只有 273/343 = 0.796，
{m2..m8} 达 399/343 = 1.163。原因是 2..8 段提供 **6 个可用顺子**（234…678），1..7 段只有 5 个（123…567）。

**187 个 U 的扫描**（`k3_summary.json`）：唯一过线者就是它；次高 {m1..m8}=0.852、{m1..m7}=0.796、9m=0.650、9m+2z=0.408。
**解析截断**：N(U) ≤ 2,846（严格口径全局类数）⇒ N+L ≤ 5,692 < |U|³（当 |U| ≥ 18）⇒ |U| ≥ 18 的 U 永远不可能否证。

**独立复核（已做）**：两条完全不同的 W 实现（`lower.py` 的 `waits()` vs 独立 `win14`）对 5,628 手听牌手牌完全一致；
L 用 84 个 3-多重集码与类内每手牌**显式取交**；每类附 blocker 表；自检 U={m1..m9} 得 N=387、L=87 与 T3 一致。
复现：`python -u work/lowerbound/k3_verify_disproof.py`（约 5 秒）。

## 4. k=4 修复进度（未完成，明天继续）

**底稿 `work/strategy/out/plan_k4_v2.json`**（designer 交换码版）：2,846 类 / 411,541 条有序码（全部不同）/
0 空类 / 0 超容量（最大用量 24 = p₄ 上限）；残余 **Type I 未覆盖 47 块** 与 **chiitoi 缺 3,926 个族码**。

**我这一轮做了什么**
1. 写了 `work/strategy/out/repair_v3.py`：chiitoi 随机换划分（7,7,7,6,6 → 93 对）+ 深度 ≤3 链式换码，Type I 链式换码。
   **但它在 `table_lib.build()` 上阻塞数分钟**（构建 PROF_I/PROF_II 很慢），未跑完。
2. 改用轻量脚本 `work/strategy/out/fix_chi_v3.py`（不加载 table_lib，14 秒跑完）：
   对 97 个 (类, z) 各随机试 600 个划分，取缺失最少的划分并把可安装的码全部装入。
   **结果：修好 0 个 / 失败 78 个（新增 3,180 条码，残余不变）**。
3. **根因（重要，已定位）**：`work/strategy/out/diag_chi2.py` 显示
   **全部 97 个 (W,z) 的"饱和码图"里都存在 K6**——即存在 6 张非 z 牌，其两两组合对应的多重集
   `(z,a,a,b)` 全部已满（usage = 12/12）。例：z=3m 时 528 对里 246 对已饱和、仅 20 对完全空闲。
   ⇒ **单纯换划分（改族设计）无法解决 chiitoi 残余；必须先把容量从饱和多重集上换出来**，
   或改用其它形状的码（`(z,a,b,c)` / `(a,a,b,c)` / `(a,a,b,b)` 也能命中 6 对七对手牌，因为手牌里有 12 张可用的对牌）。
4. 我这一轮产出的 `plan_k4_v3.json` 因未取得进展已改名为 `plan_k4_v3_aborted_chi_only.json`（**不要使用**，它只多占了容量）。
   **当前唯一有效 plan 仍是 `plan_k4_v2.json`。**

**明天第一件事（建议）**
- 路线 A（推荐，机械且成功率高）：先用**形状更宽**的码覆盖 chiitoi——
  对手牌 H = z + 2K（K 为 6 张对牌），可用的 4 码形状为
  `(z,a,a,b)`、`(z,a,b,c)`、`(a,a,b,c)`、`(a,a,b,b)`（a,b,c ∈ K）。把"每 6 集 K 必被某条已分配码命中"
  作为覆盖判据，对 97 个 (W,z) 做贪心选码（优先选未被占满的多重集），预期比 93 对族省得多。
- 路线 B：实现真正的链式换码（需要 table_lib 的 `units()/am_of()`，即"nu ⊆ am'(C', mu)"），
  把占据 `(z,a,a,b)` 的其它类的码挪走。**table_lib.build() 需后台跑（数分钟）**，别在前台等。
- 验收线：**Type I 未覆盖 = 0 且 chiitoi 未覆盖 = 0**，然后交 verifier 终验（`resid_check.py` + `fastcov` + 10⁶ 手模拟）。
- Type I 47 块：仍需链式换码；同样受 `table_lib` 加载速度限制，建议后台跑 `repair_v3.py --time-budget 3600`（注意：该脚本的 Type I 全量枚举较慢）。

## 5. 注意事项 / 残留风险
1. **口径**：七对子必须是 7 种**不同**对子（4 张同牌不算两对，题面天凤规则）。口径若变，N/L/类表都会变。
2. k=3 否证**只依赖 7 张牌**的完全枚举与显式取交，不依赖全局类表；非常稳健。
3. |U| = 13..17 的 U 未穷尽（结构枚举器未写）；但 |U| ≥ 18 有解析截断、|U| ≤ 12 已全扫，且否证 U 只有 7 张，不影响结论。
4. k=4 的 plan 修复**未完成**：v2 仍是唯一有效 plan；v3 只有一份失败尝试（已改名）。

---

## 6. 追加（新一天）：k=4 独立终验脚本 + 一个自实现 bug 的修复

### 6.1 新交付
| 文件 | 说明 |
|---|---|
| `verify_k4_plan.py` | **独立** k=4 终验脚本（不 import verifier 模块）：①类集=2846 ②0 空类 ③有序码唯一/容量 ④每码 ⊆ 该类某手牌 ⑤Type I 补牌族 DFS ⑥chiitoi 97 描述子**精确**判定 ⑦国士 ⑧10⁶ 手模拟 |
| `VERIFY_K4.md` | 脚本说明 + 每个检查的实现 + 基线结果 + 复跑命令 |
| `verify_k4_baseline.json` | 对 `work/verify/plan_k4_final.json` 的完整验证报告 |

复现：`python -u work/lowerbound/verify_k4_plan.py work/verify/plan_k4_final.json --sim 1000000 --json work/lowerbound/verify_k4_baseline.json`（约 11 分钟）

### 6.2 基线结果（plan_k4_final.json：2,846 类 / 411,508 码）
① 对称差 **0** ✓ ② 空类 **0** ✓ ③ 冲突 **0**、超容量 **0**（最大用量 24）✓
④ 码 ⊆ 手牌：通过 323,774，**未证实 87,734**
⑤ Type I：166,746 块，**未覆盖 47** ✓（与 designer/verifier 基线完全一致 → 脚本可用）
⑥ chiitoi：97 描述子，**失败 77**（附 bad_K 见证）⑦ 国士 **0** ✓
⑧ 10⁶ 手：听牌 384,418，无类 **0**，覆盖失败 **35,028** → 基线未通过（符合已知残余）

### 6.3 两个关键发现
1. **87,734 条"浪费码"**（≈21%）：这些码不属于该类的任何手牌。典型：九莲类 W={1m..9m} 在 global.json 里只有 1 个来源
   （I, A=311111113, m-only），plan 却给它分配了大量带字牌的码（(E,E,E,1m)、(N,N,N,1m)…）。
   **不破坏正确性**（A 只用本类的码），但白占容量——正是 chiitoi/Type I 修复最需要的容量。
   （caveat：以 global.json 来源清单完备为前提。）
2. **我自己 `waits()` 的一个真 bug（已修，重要）**：`melds_only` 把长度 7 的**字牌**类别也允许组顺子
   （W,N,E 被当作顺子），含字牌手牌会凭空多出听牌。修复：只有长度 9 的数牌类别允许 i,i+1,i+2 顺子。
   - 修复后与 `work/verify/indep_core`、`work/strategy/mjlib` 在抽查手牌上一致；
   - **T3/T8 结论不受影响**（只在单花色子宇宙用 W，且已双实现交叉验证）：`lower.py --verify` 仍输出 CERTIFICATE VERIFIED，
     `k3_verify_disproof.py` 仍给 N=347 / L=52 / 399 > 343 ✓；
   - 影响范围：纯字牌全量手牌由错误的"126 类 / 5,628 手"变为正确的 **28 类 / 322 手**；10⁶ 模拟的"无类"由 7,665 降到 **0**。
   - ⚠️ 副作用提示：T8 扫描里"字牌密集"的那几个 U（H-z*、terminals6+*z 等）当时用的是未修的 waits，
     其比值可能略有偏差；但过线的那唯一 U（{m2..m8}，纯花色）不受影响，**k=3 否证结论不变**。

### 6.4 下一步（验收线）
等 verifier 新版 plan 落盘后直接复跑同一命令；通过需要 ①对称差 0 ②0 空类 ③0 冲突+0 超容量 ④0 未证实 ⑤Type I 0 ⑥chiitoi 0 ⑦国士 0 ⑧模拟 0 失败。
---

## 7. 【终局】k=4 终态方案通过独立八项验证 —— 最小可行 k = 4（闭环）

### 7.1 被验对象
- 文件：`work/verify/plan_k4_FINAL.json`
- **sha256 = b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163**（我用 hashlib 实测，与 verifier 声明一致）
- 规模：2,846 类 / **17,579** 条有序 4-码 / 0 空类 / 0 超容量（最大多重集用量 18）

### 7.2 独立八项结果（我的实现，不 import verifier 模块）
| # | 检查 | 结果 |
|---|---|---|
| ① | 类集 vs `global.json` | 对称差 **0** |
| ② | 空类 | **0** |
| ③ | 有序码全局唯一 / 多重集容量 ≤ p₄ | 冲突 **0** / 超容量 **0**（最大用量 18） |
| ④ | 每码 ⊆ 该类某手牌（A 变体表精确判据） | 通过 **17,579 / 17,579**，未证实 **0** |
| ⑤ | 逐类命中集：全块(I/II/KOK) × **全 A 变体** × 补牌族（mode=chi/nochi 过滤） | 单元 **5,571,671**，未覆盖 **0** |
| ⑥ | chiitoi **97** 个描述子（精确搜索，非抽样） | 失败 **0** |
| ⑦ | 国士（13 面 + 12 种带一对，按类重建） | 失败 **0** |
| ⑧ | 随机 **10⁶** 手模拟 | 听牌 384,418 手；无类 **0**；覆盖失败 **0** |

**`VERDICT_k4_plan_ok = true`**　报告：`work/lowerbound/verify_k4_FINAL.json`　日志：`work/lowerbound/verify_k4_FINAL.log`

**跨实现一致**：我的 ⑤ 单元数 5,571,671 ≈ verifier 的「I 基式 168,817 + II 基式对 5,402,697 = 5,571,514」（差 157 = KOK 块计数口径）。

### 7.3 复现命令
    python -u work/lowerbound/verify_k4_plan.py work/verify/plan_k4_FINAL.json --sim 1000000 --json work/lowerbound/verify_k4_FINAL.json
    # 约 5.5 分钟（其中 ⑤ 75 秒、10⁶ 模拟约 200 秒）
    python -u work/lowerbound/lower.py --verify          # k=1/2 证书: CERTIFICATE VERIFIED
    python -u work/lowerbound/k3_verify_disproof.py      # k=3 否证: N=347 L=52 399 > 343（5 秒）

### 7.4 本轮修好的两处（影响终验精度与耗时）
1. **KOK 手牌按类重建**（`k4_sources.py`）：原先 KOK_HANDS 全局池化，会让"属于类 {1p} 的手牌"替"13 张幺九类"作证（verifier 指出，导致 waste 清单差 7 条）。
   现改为：|W| = 13 → 13 张幺九各一张（唯一手牌）；|W| = 1 → 除该张外 12 张幺九各一张 + 任一张重复（12 手）。与 verifier 的 `waste_exact` 口径一致。
2. **⑤ 稀疏加速**：把"为每个补牌构造 34 元手牌再做包含判断"改为稀疏 `hitA/hitAB`（直接在 (Xv+F) 上按码的 (牌,重数) 判定），
   判据完全不变（仍是全 A 变体 × 全补牌族），⑤ 从预计 **~36 分钟 → 75 秒**。
   顺带在上一版 `plan_k4_leadC_patched.json` 抓到 1 条 ④ 未证实码（类 {1p} 的 (1p,1p,1p,5p)），FINAL 版已消除。

### 7.5 上下界闭环（最小可行 k = 4）
- k=1：清一色 Στ = **427 > 34**（`certificate.json`）
- k=2：Στ ≥ **447 > 9² = 81**（同上）
- k=3：U = {m2..m8}，N = 347、L = 52 ⇒ **399 > 343 = 7³**（`k3_disproof_certificate.json`）
- k=4：`plan_k4_FINAL.json` 显式策略**通过独立八项验证**（本节）
⇒ **最小可行 k = 4（答案 = 4）**，上下界均由独立实现锁定。
---

## 8. Lean 线（T12 / `lean/Mj/Disproof.lean`）：信任基分类与未形式化的桥

### 8.1 交付与构建
- 文件：`lean/Mj/Disproof.lean`（import `Mj.Basic` / `Mj.Lemma` / `Mj.Protocol`）
- 构建命令与实测：`cd lean; lake build Mj.Disproof` → **Build completed successfully (5 jobs)**，耗时 **1078 s**，**无 sorry**（所有定理的 axioms 列表均无 `sorryAx`）
- 单文件检查：`cd lean; lake env lean Mj/Disproof.lean`

### 8.2 Lean 计算出的数值（全部由 Lean 求值，非手写常量）
| 定理 | 内容 |
|---|---|
| `flush_counts` | 93,600 手 / 40,196 听牌 / **Nflush = 387** / **L1 = 40** / **L2 = 53** |
| `u7_counts` | 7,875 手 / 5,628 听牌 / **N7 = 347** / **L3 = 52** |
| `k1k2_gaps` | `34 < Nflush + L1` ∧ `9^2 < Nflush + L2`（427 > 34、440 > 81） |
| `k3_gap` | `7^3 < N7 + L3`（**343 < 399**，k=3 不可行的核心算术） |

### 8.3 axioms 分类（`lake build` 实测输出，原样）
    'Mj.flush_counts'             depends on axioms: [flush_counts._native.native_decide.ax_1_1]
    'Mj.u7_counts'                depends on axioms: [u7_counts._native.native_decide.ax_1_1]
    'Mj.sum_ge_length_add_count'  depends on axioms: [propext, Quot.sound]
    'Mj.budget_sharp'             depends on axioms: [propext, Classical.choice, Quot.sound]
    'Mj.k1k2_gaps'                depends on axioms: [k1k2_gaps._native.native_decide.ax_1_1]
    'Mj.k3_gap'                   depends on axioms: [k3_gap._native.native_decide.ax_1_1]
    'Mj.no_feasible_k3_of_bridge' depends on axioms: [propext, Classical.choice, Quot.sound,
                                                      k3_gap._native.native_decide.ax_1_1]
    'Mj.budget'                   depends on axioms: [propext, Classical.choice, Quot.sound]      -- Mj/Lemma.lean
    'Mj.classes_le_pow'           depends on axioms: [propext, Classical.choice, Quot.sound]      -- Mj/Lemma.lean
    'Mj.no_common_code_two'       depends on axioms: [propext, Quot.sound]                       -- Mj/Lemma.lean

- **只用内核公理（propext / Classical.choice / Quot.sound）**：
  `sum_ge_length_add_count`、`budget_sharp`、`u7_nodup`、`u7_length`，
  以及 `Mj.Lemma` 的 `budget` / `classes_le_pow` / `no_common_code_two`。
- **依赖 native_decide（Lean.ofReduceBool 编译器信任）**：
  `flush_counts`、`u7_counts`、`k1k2_gaps`、`k3_gap`。
- **含显式桥接假设 hbridge（未形式化）**：`no_feasible_k3_of_bridge`。

### 8.4 hbridge 语义（**未形式化的桥，不是已证事实**）
`no_feasible_k3_of_bridge` 的前提 hbridge 断言：
「`Feasible 3` ⇒ 存在类族 `cls` 与谓词 `bad`，满足 `budget_sharp` 的全部假设，
且 `cls.length = N7`、`(cls.filter bad).length = L3`」。
其证明需要以下四条，**均尚未形式化**：
 (a) `codesU` / `subsOfSize` 的枚举完备性引理（码空间 = 全部 "⊆ U 的 k-重集"）；
 (b) `classKey : List Nat` ↔ `waits : List Tile` 的桥接；
 (c) `coversAll` ⇒ 每类「预算内码集」非空；
 (d) 无公共码的类 ⇒ 其码集大小 ≥ 2（唯一码被覆盖性要求命中全类 ⇒ 与"无公共码"矛盾）。
⇒ 该定理是**骨架 + 显式假设**；报告/README 中不得当作已证结论引用。

### 8.5 内核 `decide` 的实测与回退
内核级 `decide` 跑 7,875 手枚举：**本机 10 分钟内未完成**（kernel whnf 爆炸），
已**回退到 native_decide**（文件头与注释均标注"依赖 Lean.ofReduceBool（编译器信任）"）。
若要把 §2/§3 也做成完全内核级，需走「**证书 + 内核校验**」路线：
把 347 个类键与 52 个无公共码类的见证对作为字面量落盘，由内核逐条校验（本轮未做）。
---
## 9. Bridge.lean 状态（T15）：**已完成（hbridge-free）** —— k=1 / k=2 / k=3 否证

### 9.1 构建状态（本轮由 analyst-lower 修复并验证）
- 文件：`lean/Mj/Bridge.lean`
- 单文件：`lake env lean Mj/Bridge.lean` → **exit 0，无 error、无 sorry**（原 2 条 linter 提示已清理）
- 全库：`lake build` 需先让 Bridge 进入默认目标（见 §9.7 的 Lake glob 教训）。
  Lead 已在 `lean/Mj.lean` 补 `import Mj.Bridge`，全库构建（含 Bridge）由 Lead 统一跑并报告；
  **analyst-lower 交付时点**：Bridge 单文件 = 绿色；`lake build`（不含 Bridge 的旧目标）= 9 jobs 全绿。
- 文件内**无 sorry、无新 axiom、无 hbridge**；原「缺口 1/2/3」（keysU/badKey 等价性、badOf_iff、§4 引理 tactic）**全部不再需要**：
  改用更短的「只看类数」路线，无需 L3=52 / badOf / badKey。

### 9.2 论证（比原计划更短）
对 U 与 k：令 keys := U 内「13 张且听牌」手牌的**去重类键**（`keysOf U src`）。
对每个 W ∈ keys 取 S_W := P.codesOf W 中「长度 = k 且元素全在 U 内」的码（`SC P U k W`）。
- **每类非空**：coversAll 给出码 c；HandContains 给出 c 的 support ⊆ H 的 support；inU 给出 support ⊆ U；
  Plan.valid 给出码索引都 < 34（唯一附加假设，见 §9.4）。
- **不同键 ⇒ 码集不交**：Plan.disjoint。
- ⇒ Σ_W |S_W| ≤ |U|^k（`Mj.Lemma.budgetNat` + `seqN_length`，码池 = seqN U k 且 |seqN U k| = |U|^k）。
- 每类 |S_W| ≥ 1 ⇒ Σ_W |S_W| ≥ keys.length = N。
- ⇒ 若 |U|^k < N，则不存在满足 lengths k ∧ coversAll k ∧ disjoint ∧ valid 的表 P（`Mj.noFeasible_of`）。

### 9.3 三条主定理
| 定理 | U | k | N（普查） | 码池 | 结论 |
|---|---|---|---|---|---|
| `Mj.no_feasible_k1` | u9N（前 9 张） | 1 | 387 | 9^1 = 9 | k=1 不可行 |
| `Mj.no_feasible_k2` | u9N | 2 | 387 | 9^2 = 81 | k=2 不可行 |
| `Mj.no_feasible_k3` | u7N = {1..7} | 3 | 347 | 7^3 = 343 | k=3 不可行 |

计数定理（各自一次 native_decide，不在库内重算第二次）：
- `keysFlush_count : (keysOf u9N flushHands).length = 387` —— 与 `Mj.flush_counts` 的 Nflush = 387 **独立普查、数值一致**。
- `keysU7_count : (keysOf u7N u7Hands).length = 347` —— 与 `Mj.u7_counts` 的 N7 = 347 **独立普查、数值一致**。

### 9.4 建模假设（必须交代）
`Plan.valid P := ∀ W c, c ∈ P.codesOf W → ∀ x ∈ c, x < 34`。
因为 `HandContains` 只对 `Fin 34` 量化，`coversAll` 本身不排除「码里含 ≥ 34 的索引」；
`Plan.valid` 排除这类退化表（协议语义：A 只能摆真实存在的牌）。
**这是本否证唯一附加的建模假设**，且远弱于原 hbridge（一行定义，无需枚举完备性论证）。

### 9.5 实测 axioms（`#print axioms` 已固化在文件末尾）
    'Mj.noFeasible_of'   depends on axioms: [propext, Classical.choice, Quot.sound]
    'Mj.no_feasible_k1'  depends on axioms: [propext, Classical.choice, Quot.sound, keysFlush_count._native.native_decide.ax_1_1]
    'Mj.no_feasible_k2'  depends on axioms: [propext, Classical.choice, Quot.sound, keysFlush_count._native.native_decide.ax_1_1]
    'Mj.no_feasible_k3'  depends on axioms: [propext, Classical.choice, Quot.sound, keysU7_count._native.native_decide.ax_1_1]
⇒ 通用引擎 **完全内核级**；三条主定理的信任何 = 对应普查计数那一条 native_decide（编译器信任）；
**无 hbridge、无 sorryAx**。（`keysFlush_count` / `keysU7_count` 自身也各只有那一条 native 公理。）

### 9.6 与 Mj.Disproof 的关系
- `Mj.Disproof.no_feasible_k3_of_bridge` 依赖未形式化的 hbridge ⇒ **已被取代**（Disproof.lean 内已加 ⚠️ SUPERSEDED 注释）。
  保留作历史对照：它含 L3 = 52 的加强下界与内核引理 `budget_sharp`（`347 + 52 ≤ 343` 的更精细版本）。
- Bridge 中除 2 条计数定理外的全部内容（dedupAux 系列、mem_seqN / seqN_length、budgetNat、noFeasible_of）都是真证明，只用 propext / choice / Quot.sound。

### 9.7 工程注记（性能 / Lake 目标）
- **不要在 Bridge 内把普查写回主定理之外**：早期版本在 Bridge 内额外重算 U7 普查 ⇒ `lake build Mj.Bridge` 在 2196 s 后
  以 `0xFFFFFFFF` 退出（大闭项内存耗尽）。现在每个计数只留**一条** native_decide 定理。
- 完整构建时间量级：Bridge 单文件 ≈ 10–15 min（两条普查的 native 编译/执行占绝大部分）；全库 `lake build` 需重编 Disproof + Bridge。
- **⚠️ Lake 的 module glob 在配置期缓存**：新建的 `Mj/Bridge.lean` 一开始**不会被 `lake build` 编译**
  （`.lake/build/lib/lean/Mj/Bridge.olean` 根本不出现，即使 `lake build` 报 "Build completed successfully (9 jobs)"）。
  根因：Bridge 没有被任何模块 import，而 Lake 的库模块清单在 configure 期已缓存。
  **修法（Lead 已实施）**：在 `lean/Mj.lean` 里补 `import Mj.Bridge`（同理 `import Mj.Data` / `Mj.Upper` / `Mj.Data2` / `Mj.Upper2`），
  之后 `lake build` 才会连带编译它。**教训：新增 Lean 模块后必须显式 import（或重新 configure），
  不能只看 `lake build` 的 jobs 数就以为覆盖了新文件。**

