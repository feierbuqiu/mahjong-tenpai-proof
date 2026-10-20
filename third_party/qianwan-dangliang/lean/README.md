# Lean 形式化：麻将「翻牌猜听牌」最小翻牌数 k = 4

环境：Lean 4.33.1（lean-toolchain 已固定），只用 core/Std（本机无 mathlib，Std 不含 Finset，故集合用 List，手牌用 Array Nat 计数向量）。
命令：cd lean; lake build；单模块：lake build Mj.Upper；脚本：lake env lean 文件名.lean。

## 模块与状态

| 文件 | 内容 | 状态 |
|---|---|---|
| Mj/Basic.lean | 牌/手牌/和牌判定（标准型 4 面子+1 雀头、严格七对子=7 种不同牌各 2 张、国士无双=仅幺九牌）、听牌、码包含、枚举 | 编译通过；与已验证 Python 实现交叉对拍 **31875 手**（含 15143 听牌；覆盖 U={m2..m8} 全部 7875 手、单花色 2 万手、七对子/国士/字牌/非听牌）**0 失配** |
| Mj/Protocol.lean | 协议模型（classKey/Plan/coversHand/coversAll/disjoint/lengths/Feasible）+ 解码表与解码正确性 | 全部真证明；decode_unique 不含任何公理，decode_correct 仅 propext/Quot.sound |
| Mj/Lemma.lean | 子宇宙预算引理：seqU/codesU + mem_codesU/codesU_nodup/codesU_length + budget + classes_le_pow + no_common_code_two + contains_eq_true_iff | 真证明（budget/classes_le_pow 依赖 propext/choice/quot），无 sorry/无自定义 axiom |
| Mj/Disproof.lean | k=1/2/3 否证：单花色 93600 手（听牌 40196、387 类、L1=40、L2=53）；U={m2..m8}（7875 手、听牌 5628、N=347、L3=52）；budget_sharp；no_feasible_k3_of_bridge | **lake build 通过（1078 s）、无 sorry**；数值全部由 Lean 计算；hbridge 为显式语义桥接假设（未形式化桥，见下） |
| Mj/Bridge.lean | **hbridge-free 否证线**：通用引擎 noFeasible_of（U 内听牌类数 N > 码池 \|U\|^k ⇒ k 不可行）+ no_feasible_k1 / k2 / k3（U=前 9 张 N=387 > 9^1=9、> 9^2=81；U={1..7} N=347 > 7^3=343） | **lake env lean 通过、无 sorry / 无 hbridge**；通用引擎 axioms = propext/choice/Quot.sound；三条主定理仅额外依赖各自普查计数的 native_decide；唯一附加假设 Plan.valid（码索引 < 34） |
| Mj/Data.lean | 由 plan_k4_FINAL.json 生成：planData（2846 类 / 17579 条有序 4 元码）、iUnitData（168817 个 I 型单元）、fillOf（8706 个补牌族向量） | 2.40 MB / 3013 def；**Lead 独立核验：Lean 的 planData 与 Python 方案逐条一致（2846 类、键差 0、码集差 0）** |
| Mj/Upper.lean | blockCovered（块级 DFS 语义）+ 结构检查 + 覆盖检查 | lake build Mj.Upper 通过（约 210 s，含 native_decide 代码生成与编译） |
| Counterexample.lean | 用 Lean 反例机器验证的两处语句缺陷（budget 缺 Nodup 假设、推论②缺元素合法性假设） | 退出码 0 |

## 检查结果

1. I 型块级语义：全部 168817 个块通过（iBlocksAllCovered_true = true），与 Python 的 work/verify/block_coverage_exact.py 的 I_uncovered = 0 一致。
2. 结构：码长全为 4、17579 条有序码全局唯一、2846 类全非空（structOk_true = true）。
3. 说明性结论：若把覆盖判据退化为『存在单条码 c 包含于活性部 A』，则 I 型有 169 个单元反例（去重后 135 个 (类,单元) 对），全部落在 34 个单张类的 tanki/size-4 块——这正是必须使用块级补牌族语义的原因（tanki 块靠 (z,M0,M1,M2) 族覆盖）。
4. II 型 5402697 个单元未内联；外部脚本对全部单元做严格检查：5402581 通过 / 116 与 I 型同类；块级语义下 II_uncovered = 0（Python）。

## 信任基（实测 #print axioms）

| 定理 | 依赖 |
|---|---|
| decode_unique | 无公理 |
| decode_correct | propext, Quot.sound |
| budget, classes_le_pow | propext, Classical.choice, Quot.sound |
| no_common_code_two | propext, Quot.sound |
| structOk_true | native_decide 的 Lean.ofReduceBool 机制 |
| iBlocksAllCovered_true | propext + native_decide 机制 |
| checkPlan_true | propext + native_decide 机制 + 唯一数学 assumption iiUnitsComplete |
| flush_counts, u7_counts | native_decide 机制（编译器信任）：93600/40196/387/40/53 与 7875/5628/347/52 |
| sum_ge_length_add_count, budget_sharp | propext, Classical.choice, Quot.sound（内核级，无编译器信任） |
| k1k2_gaps, k3_gap | native_decide 机制：34<427、81<440、343<399 |
| no_feasible_k3_of_bridge | ⚠️**已被取代**：propext, choice, Quot.sound, k3_gap 的 native 机制 + **显式桥接假设 hbridge**（文件内已加 SUPERSEDED 注释；请改用下一行） |
| noFeasible_of (Bridge) | propext, Classical.choice, Quot.sound（纯内核） |
| no_feasible_k1 / k2 (Bridge) | 上述内核公理 + keysFlush_count 的 native_decide 机制（387） |
| no_feasible_k3 (Bridge) | 上述内核公理 + keysU7_count 的 native_decide 机制（347） |

**唯一数学 assumption**：iiUnitsComplete（II 型 5402697 个单元的块级覆盖未在 Lean 内验证；外部已全量检查并如实披露 116 个严格判据反例）。
**native_decide 说明**：Lean.ofReduceBool 是 Lean 编译器的可信基。关键的小规模算术（U={m2..m8}）已在 Mj/Disproof.lean 中尽量用内核 decide 复核，大规模普查交给 native_decide 并如实标注。

## 与 Python 流水线的关系

同一个数学结论有两条独立验证线：
* Python 线（三重独立实现）：work/verify/fastverify_k4.py + block_coverage_exact.py（逐块 I+II 精确 DFS）、work/lowerbound/verify_k4_plan.py（八项含 10^6 手模拟）、work/recon/k4_gap_par.py（Lead，numpy+12 进程）；否证证书 work/lowerbound/k3_disproof_certificate.json 与 certificate.json。三者对同一 sha256 b95f5523... 的文件结论一致。
* Lean 线：同一套定义与引理的形式化，并独立复算关键数值（93600/387/40/53 与 7875/347/52），以及协议解码正确性的真证明。
两条线共用同一判定口径（严格七对子、字牌不组顺子、国士仅幺九牌），并由 Mj.Basic 与 Python indep_core.compute_W 的 **31875 手**交叉对拍绑定；此外 **Lean 的 planData 与 work/verify/plan_k4_FINAL.json 已逐类逐码对拍一致（2846 类、键差 0、码集差 0）**（脚本 work/lean/check_data_consistency.py，导出 lean/DataDump.lean）。

**内存实测**：Lean 内联巨型字面量不可行——200,000 个 Nat 字面量（1.32 MB 源文件）编译 300 s 时峰值内存 2,256 MB 且仍在增长；外推 5,402,697 单元（≈40–50 MB 源码）需数十 GB ⇒ 必须走 Data2 的『块记录 + Lean 内枚举』路线（详见 work/recon/LEAN_MEM_ESTIMATE.md）。
