# HANDOFF — enum-core（写作用域 work/data/）

## 1. 状态：**已完成**（task-1、task-2 均已 complete）

最后跑通的命令与结果：

    python -u work/data/census_single.py   # -> work/data/out/single.json      (~4s)
    python -u work/data/census_two.py      # -> work/data/out/global.json      (~63s, 6 进程)
    python -u work/data/_tau_cert.py       # -> work/data/out/cert_tau.json    (~8s)
    python -u work/data/_probe3.py         # 暴力法交叉验证（0 mismatch）
    python -u work/data/_probe12.py        # 全局表 vs 单类别独立普查
    python -u work/data/_probe13.py        # 补牌族最小值 + mincount 判据
    python -u work/data/_tau_validate.py   # 集合覆盖算法 vs 暴力穷举（545 实例 0 mismatch）

- **全局听牌类数 = 2,846**（严格七对子口径：7 种不同牌各 2 张）。|W| 分布
  {1:34, 2:561, 3:894, 4:738, 5:372, 6:156, 7:69, 8:18, 9:3, 13:1}。
- 无公共码类数 k=1/2/3/4 = 1789/1822/1924/1996；Σ_C K(C) = 7213。
- 34¹/34²/34³/34⁴ = 34/1156/39304/1336336 ⇒ **2846 > 1156，k=2 死**；**2846 < 39304，类计数不否证 k=3**。
- 清一色 m/p/s：13 张全集 **93,600**、和牌 13,259、听牌 40,070（标准型）/40,196（完整 W）、类 **387**、无公共码 40/53/87/111。
- 字牌 z：听牌 315/322、类 28、无公共码 0/7/7/7。国士 157 手 / 14 类。
- 全部听牌手牌 **92,371,838** = 54,747,045（标准型）+ 37,657,312（七对子）− 32,676（重叠）+ 157（国士）。

## 2. 交付物清单

| 文件 | 说明 |
|---|---|
| `work/data/mjcore.py` | 核心库：34 张牌模型、和牌判定（标准型/七对子/国士）、W(H)、主动-惰性分解、V/Wp/pd/melds_pair 闭式原语、M_k 码集与公共码判据 |
| `work/data/census_single.py` | T1 普查：直接枚举清一色全部 93,600 手 / 字牌 7,875 手，+ 国士 |
| `work/data/out/single.json` | T1 数据：每类 W、逐手牌清单（count 串）、mincount、K、k=1..4 公共码 |
| `work/data/STATS_single.md` | T1 完备性论证 + 数字 + 两个口径区分 + 旧数字勘误 |
| `work/data/census_two.py` | T2 全局普查：Type I/II 主动部 + 七对子逐手枚举 + 国士 |
| `work/data/out/global.json` | **权威全局类表**（17.5MB）：W、mincount、K、公共码、n_hands、sub_universe、sources（I/II/tanki/chiitoi/kokushi） |
| `work/data/STATS.md` | T2 方法/完备性/数字/子宇宙 τ/复现命令 |
| `work/data/out/cert_tau.json` | 子宇宙 τ 证书：每类 lb、ub、exact、**实际命中集码列表**（生成时逐手验证覆盖） |
| `_probe3/8/10/11/12/13.py, _tau_*.py` | 校验与 τ 计算脚本（保留以便复核） |

## 3. 已知 bug / 未收敛的原因

1. **今天真正未收敛的是 T4 的 k=3 全局装包**（不在我职责内）；k=3 是否可行仍未知。
   子宇宙路线已排除否证：Στ_m ∈ **[554, 564]** ≤ 729、Στ_z ∈ [28, 42] ≤ 343。
2. **我这边唯一的未收敛点**：4 个最大清一色类 W={3m},{7m},{2m},{8m}（n=1873~3003）的 τ 未全部证明最优。
   {2m}、{8m} 已证 τ=7（无时限 B&B）；{3m}、{7m} 目前只有 LB=2 / UB=7。
   ⇒ Στ_m 最可能 = **564**。Lead 报的 **566 比我的严格上界 564 大 2**，原因未查明（见 §5）。
3. 我修掉的两个自家 bug（已不影响交付，记录以免重犯）：
   - `_tau_flush.py` 初版候选码未做**重数校验**（(x,x,y) 只检查 1 张 x）⇒ τ 被系统性低估；
   - 初版 B&B 未先取贪心上界 ⇒ 剪枝失效，单个类跑到 900s。修好后 60 个开放类中 56 个在 600s 内精确关闭。
4. Lead 的 recon 脚本（已知，供 REPORT 记录）：`recon_counts.py` 的"标准型和牌"分支实际产出 0 手
   （其 37,657,469 = 37,657,312 七对子听牌 + 157 国士听牌，**不是**"全部听牌手牌总数"；5,379,616 = C(34,7) 是七对子**和牌**数）；
   `recon_flush.py` 的 `gen_run_vecs` 无法生成重复面子 ⇒ 26,680/383 是错的（真值 40,070/387）。
5. MODEL.md §5 的"七对子听牌 ⇔ 恰一种牌奇数张且张数 ∈{1,3}"是**奇偶/豪华七对**口径，与 §6.0 裁决的严格口径冲突；
   该（已作废）口径下我精确枚举全部 100,728,672 手"恰一奇数计数"手牌，得全局类数 **15,592**（不是 9,164），仅作记录。
6. 注意 `recon_flush` 遗留的"93,516"：13 张单花色多重集总数应为 **93,600**
   = C(21,13) − 9·C(16,8) + C(9,2)·C(11,3) = 203490 − 115830 + 5940。

## 4. 后续接手步骤

1. **关闭最后 2 个 τ**：改 `_tau_exact.py` 的 tlimit 为 3600、只跑 {3m},{7m}（单进程，最坏 ~2h），
   若得 7/7 ⇒ Στ_m = 564，把 STATS.md 与 cert_tau.json 写死。
2. **与 Lead 对齐 566 vs 564**：逐类比对 (W, τ) 表找差 2 的类（我的每类值都在 cert_tau.json / cert_tau_bounds.json）。
3. **T4 装包输入**：直接用 `out/global.json` 的 sources 作为"来源块"清单。两个特殊块：
   - tanki 块（|A|=1，只有 34 个类，W 为单元素）：**无通用码**，需码族 {(x,a,a)} ∪ {(x,a,a+1)}（约 41–49 条）；
   - chiitoi 描述子（61 个类）：见 `chiitoi_descriptors`，覆盖需 {(z,a,a)}，a 的补集 ≤ 5 ⇒ 每个 z 至少 28 个 a。
4. **更强的 k=3 判据（可选）**：对清一色 387 类做精确**装包/Hall 匹配**（而非只比 Στ 之和）；
   或算 U = m∪p 子宇宙（|Codes_3| = 18³ = 5832）。工具：`_tau_cert.py` 的覆盖生成 + 我的位集代码。
5. 复现顺序：census_single.py → census_two.py → _tau_cert.py；全部依赖 `mjcore.py`（纯 Python 3.14，无第三方依赖）。

## 5. 需要 Lead / 其他人配合

- **Lead**：核对 Στ_m = 566 vs 我的严格上界 564（差 2）；把 §3 的 recon bug 与"严格口径裁决"写进 REPORT.md。
- **verifier**：独立复算 `out/global.json` 的 mincount（可随机抽若干类直接枚举手牌核对）并复核 `cert_tau.json` 的 lb/ub；
  也可独立核对 93,600 这个多重集总数。
- **designer-encoder**：如果装包需要"每类每来源块的覆盖需求清单"（块 → 通用码判据 → 最小码族），
  我可以从 global.json 的 sources 直接生成，说一声即可（预计半天内）。
- **通用注意**：我全程最多开 6 进程；`census_two.py` 63s、`_tau_exact.py` 单类最坏 600s、`_tau_cert.py` 8s。

---

## 附：L6（task-16）II 型 Lean 内验证 —— 收口状态（enum-core）

> 文件：`lean/Mj/Data2.lean`、`lean/Mj/Upper2.lean`、`work/lean/gen_data2.py`、`work/lean/Timing2.lean`；
> 机器可读状态：`work/lean/gen_data2_report.json`。

### 已完成（第一步）
- 规模：II 块 **309,144**、单元 **5,402,697**、profile **2,469**（16 个 (c,size) 组）。
- Data2.lean：**4.68 MB**；块记录打包为单个 Nat（rec = classIdx·2^25 + comboIdx·2^18 + k1idx·2^9 + k2idx），
  30 行切块 + 64 块一批拼接（避免 maxRecDepth 超限）；profTable 内联 (key, |xs|, Σenc)。
- **对拍不一致数 = 0**：Python 侧 2,469 个键重新枚举 vs PROFII_D 的 xs 逐条一致；
  Lean 侧 `profTableOk = true`（native_decide）——Lean 枚举 + profile 分组与 Python 表 16 组全部一致。
  （备注：table_cache 的 PROFII_D `am` 分量是 [0]*34 占位，table_lib 的 min 更新条件写错，与本次对拍无关。）

### 已实测（第二步雏形）
- `lake build Mj.Upper2` **通过**（Data2 148s + Upper2 21s，增量）。
- 严格单码判据（∃ 码 ⊆ X1⊎X2）子集：前 1,000 块 = 18,336 单元失败 0；
  前 20,000 块 = 486,754 单元，**失败块 20 / 失败单元 21**。
- 该 20/21 已由 Python 独立复核（`work/lean/probe10.py`）得到完全相同数字 ⇒ Lean 检查器正确，
  失败真实（这些块没有单条通用码，与 I 型 169 反例同源）。

### 缺口（未验证，勿当作已验证）
- **剩余 289,144 块 / 4,915,943 单元未在 Lean 内跑**（本轮 9.0%）。
- `iiBlockCovered` 目前是**严格单码**判据，需升级为**多码/块级 DFS 语义**才能使那 20 个块通过。
- 全量预计 ≈ 2–5 分钟（依据：3 组子集共 613k 单元的求值都在 21s 的编译内完成）。
- 完成后可删掉 `Mj/Upper.lean` 的 assumption `iiUnitsComplete`。

### L6 续（第二步升级 + 全量）—— 最终诚实状态

**关键修复（Python 与 Lean 两侧都改了）**：块级 DFS 原来只用「落在 c1/c2 内的码」，但码完全可能用到
inert 类别的牌 ⇒ 严格单码检查可只用过滤后的码（code ⊆ A ⊆ c1∪c2，合法），而 **DFS 必须用该类的全部码**。
修复前误报 2,032,790 个失败单元（37.6%）；修复后：

- **Python 独立全量**（work/lean/verify_l6.py，块级语义 + 全码 DFS，8 进程）：
  **309,144 块 / 5,402,697 单元 / 失败块 0 / 失败单元 0，93.9 s**；
  逐批 16 行写入 work/lean/gen_data2_progress.jsonl（均 failed_blocks=0）与 work/lean/gen_data2_totals.json。
  注意：该 jsonl 里另有 6 字段格式的**外来行**（非本脚本产出、数字不同），请以 7 字段行 / totals.json 为准。
- **Lean 内核**：lake build Mj.Upper2 通过（333 s，含检查）；已完成的内核检查为
  blockStat ((l6Batches.getD 0 []).take 2000) = (2000, 0, 50935, 0) ⇒ **50,935 单元 / 0 失败**。
  **未完成（缺口）**：全量 309,144 块 / 5,402,697 单元的 Lean 内核 native 求值——本次会话 3 次尝试
  （28 min / 18 min / 8+ min）均被时间上限打断；l6BatchStats_eq / l6Total_eq 在 Upper2.lean 中以注释保留。
  Mj/Upper.lean 的 assumption iiUnitsComplete 仍在。
- 性能根因（已缓解）：reqOf 曾在每个 (码,单元) 对上重扫 34 张牌 → 已改为按块预计算打包需求表 codeReq2。
  剩余瓶颈与下一步：① planData → Array（codesOfIdx 现为 O(classIdx) List 遍历）；
  ② 按 (class, c1, c2) 预建需求表缓存；③ 把 16 批拆成 16 个独立 theorem，分批落盘 + 断点续跑。
