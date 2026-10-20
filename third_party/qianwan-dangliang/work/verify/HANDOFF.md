# HANDOFF — verifier (T5 / T6)

> 作者：teammate verifier ｜ 写作用域 `work/verify/` ｜ 交卷时间：本轮结束
> 口径：题目 `mahjong-question2.md` 规定「天凤规则」⇒ 七对子 = 7 对**不同**的牌（4 张同牌不算两对）。

## 1. 状态

| 任务 | 状态 | 最后跑通的结果 |
|---|---|---|
| T5 独立核心 + 交叉核对 | **完成** | 全局类数 **2,846**（strict）；清一色 **40,196 手 / 387 类 / 全集 93,600 / 无公共码 40·53·87·111**；字牌 **28 类**；与 enum-core、Lead、T3 证书**逐一一致** |
| T6a 下界证书重放 | **完成** | k=1 Στ=427>9；k=2 Στ=457（我独立精确）>81；k=3 计数法不能否证；**未发现反例** |
| T6b 构造策略终验 | **进行中** | **k=3 已被否证（k_min ≥ 4，verifier 独立重放通过）**；k=4 plan_k4_v2.json：结构基本合格（2846 类/0 空类/411,541 有序码唯一/0 超容量）但 (a) Type I 47 块、(b) chiitoi 精确 77 个描述子失败、(c) 30 万手模拟 8,301 失败、另有 33 条废码 ⇒ **k=4 上界尚未锁定** |

验证器就绪、随时可跑：`python -u work/verify/verify_strategy.py 1000000 <plan.json>`（约 4–6 分钟）。
最后一份被验证的 plan 是 `work/strategy/out/plan.json`（22:05）：2846 类、W 集合与我的独立类集完全一致、5490 个有序码 0 复用、多重集容量 0 违例，
但 **995 个类没有任何码**，且有码类仍有大量覆盖缺口（见 §3）。

## 2. 交付物清单

| 文件 | 说明 |
|---|---|
| `indep_core.py` | 独立核心：pending-run DP 面子分解、34 张全量和牌判定（字牌禁用顺子）、W(H)、清一色枚举、闭式 W |
| `census.py` | 独立全局类普查（签名法，loose/strict 双口径 + 缩小宇宙 brute-force 对拍模式） |
| `tau_flush.py` | 独立 B&B 最小命中集：清一色 Στ_m、字牌 Στ_z |
| `cert_replay.py` / `replay_cert.py` | k=1/k=2 子宇宙预算重放；T3 证书逐类对拍 |
| `verify_strategy.py` | **T6b 主验证器**：类集完整性 / 有序码全局唯一 / 多重集容量 / Type I 补牌族 DFS 完备覆盖 / 全部单类别手牌逐手覆盖+反向解码 / chiitoi 组合 / 国士 / Monte-Carlo |
| `gap_exact.py` | 对任意 plan 精确统计覆盖缺口（空码类、未覆盖手牌数、未覆盖来源块、chiitoi 缺口） |
| `cross_check.json` + `CROSS_CHECK.md` | 我的数字 vs 队友/Lead 参考值的差异表 + 我找到的 4 个缺陷 |
| `VERIFY.md` | T6 终验报告（结论、覆盖度、残留不确定性、复现命令） |
| `census_strict.json` / `census_loose.json` | 我的 2846 / 15592 个类（W 列表，可直接与任何实现 diff） |
| `cert_k1_k2.json` / `cert_replay_report.json` / `verify_report.json` / `gap_exact.json` | 机器可读的验证结果 |

## 3. 已知 bug / 未收敛原因

### 3.1 我自己的 bug（都已修，特此披露）
1. **加所听牌未查 4 张上限** → 清一色多出 676 手假听牌（40,872 vs 40,196）。已修。
2. **Type II 雀头类判据用了「有对子」**，正确是 `melds_pair(X)`（能拆成面子+雀头）。pd 版 30,000 手随机手牌里 41 手闭式 W ⊋ brute force W；修正后 200,000 手 0 失配。
3. **严格七对子听牌判据**应写 `sum(x==2)==6 and sum(x==1)==1`。
4. **字牌不能有顺子**（最严重）：通用 DP 会把 7 张字牌当花色，使我的全局普查多出 440 个假类（3286 → 修正后 2846）。
5. 空惰性补牌族 `lazy_all2_exists(0)` 误判 False（使七对子附加分支为空；修正后总数不变 2846）。
6. **验证器 Type I 块 DFS 首版有 bug**（叶子把 rem==0 当已覆盖、分支聚合用 any），误报「162,363 块 0 uncovered」。**已撤回**，修正后为 99,305 块未覆盖。
7. 曾用「按多重集去重」判码不交，误报「码数不足」；**已撤回**：码是有序元组，同一多重集的至多 p(m)∈{1,3,6} 个排列可合法服务多个类。

### 3.2 团队侧（我复核发现的）问题
- recon_counts.py 的 37,657,469 与 recon_flush.py 的 26,680/383 都有 bug（前者=严格七对子手牌 7·C(34,7)+国士 157；后者漏重复顺子）。
- MODEL.md §5 的「恰一种牌奇数张」、§4/§6.2 的 Type II pd 判据都需要按 §3.1 的口径修正。
- **k=3 plan 的真实卡点不是预算而是分配器**：清一色 Στ_m ≤ 565（可行分配 676/729 ✓）、字牌 Στ_z=42（≤343），全局 34³=39304 对 2846 类绰绰有余；但公开 plan 里空码类 995 个（217 单类别 + 778 两类别）、有序码虽 0 复用却仍有 73,305 个有码类的 Type I 块未被覆盖、chiitoi 有 70 个有码描述子未覆盖。

### 3.3 k=4 plan 的验证结论与根因（2026-09-16）
- `work/strategy/out/plan_k4.json` **17:42 版**：类集合 / 有序码唯一性 / 码格式 / 字牌覆盖 / 反向解码全部 ✓；但 **9 个空码类** + 有码类中 m 15 / p 17 / s 18 个类有覆盖缺口（合计 20,194 手未覆盖）+ Type I 来源块 35,602 未覆盖。
- **17:52 版（最新，复验完成）**：有序码 13,364 全部唯一 ✓、类集合 ✓、字牌 100% ✓；**空码类反而增加到 75 个**；有码类未覆盖手牌降至 **7,275 手**（m 2,612 / p 2,246 / s 2,417）。
  关键观察：缺口最大的那些类**已经有本门码**（`has_local_code=True`）却仍有一批手牌没被覆盖 ⇒ 症结是**类内覆盖不完整**（同一类不同来源块需要不同本门码），不是本门池不足；另有 s 门 {3s,6s,9s} 完全无本门码（442 手全未覆盖）。逐类清单见 `work/verify/k4_gap_classes.json`。
- **根因**：类 {1m,4m}（及同结构类）分到的码全是 `(2m,3m,X,X)`（X∈{p,s,z}），而该类含全 m 清一色手牌（13 张全在 m）⇒ 码永远装不进，1,377 手全未覆盖。
  规则：**凡含「全落某门 U」手牌的类，必须至少有码落在 Codes(U) 内**；每门 9⁴ = 6561 是真实约束资源。
- 诊断工具：`python -u work/verify/k4_gap_classes.py <plan>` 输出「需修类清单 + 每类未覆盖手牌数」；`python -u work/verify/gap_exact.py <plan>` 出总量。

### 3.4 k=4 备份路径现状（2026-09-16 晚，按 lead 要求归档）

- **容量墙已打破**（本会话关键进展）：u9/u7 的 m/p/s 本门有序码原本 **100% 占满（6,561/6,561）**；`refit_local_k4.py` 通过「保留混门码 + 清空含单门手牌类的本门码 + 按类求贪心命中集」把每门占用降到 **~690**，首次实现四个花色单门手牌覆盖 **0/0/0/0**。
- **`plan_k4_permfix.json`（21:07 快照）**：block-level「⊆A 通用码优先 + 排列回退」把 Type I 未覆盖从 1,599 降到 **155**（其中 402 个块由 ⊆A 通用码一次修好）；lead 独立复跑：结构全过（2846 类 / 409,521 条有序码唯一 / 0 空类 / 单花色 0/0/0/0），残余 (a) 155 块、(b) chiitoi 1,196/200,000、(c) sim 8,615。
- **已定位但未修的残余原因**：
  1) (a) 是「冷门 A 的多重集排列被别的类占满」——需要**增广路/最大流**分配（左=块单元、右=多重集、容量 p(μ)），而不是贪心；
  2) (b) 我第一版鸽笼族用 6 组是**数学错误**（K 可每组取一张 ⇒ 无对命中）；正确需 **≤5 组**（α=5<6，如 7,7,7,6,6，同组对 93 条）；且 `(a,a,b,b)` 与 z 无关会被跨类抢容量 ⇒ 建议改用 **z 标记码** `{(z,a,a,b)}`（不同 z 天然不冲突；k=3 时更简单：`{(z,a,a): a 遍历 33 张}` 即覆盖所有 K）。
- **k=3 优先原则**：B 在 k=4 时只需翻 1..4 位、用前 3 个值查同一张解码表 ⇒ **k=3 可行 ⇒ k=4 可行**。因此 k=4 生成器保留为后备。

### 3.5 k=3 否证：verifier 独立重放通过（当前最高优先级结论）

- 否证对象：U = {m2..m8}（7 张）；N(U)=347 类 / L(U)=52 类（无公共 3-码）；下界 347+52 = **399 > 343 = 7³** ⇒ 与子宇宙预算引理矛盾 ⇒ **k=3 不可行，k_min ≥ 4**。
- verifier 独立重放（`work/verify/verify_k3_disproof.py`，用自己的 compute_W）：7,875 向量 / 5,628 听牌手 / N=347 / L=52 全部一致；347 个类集合与 52 个 L 类集合与证书**逐一相等**；**52 类的 blocker 表逐条校验通过**（非法手牌 0 / W 不符 0 / 见证失效 0；每类 blocker 覆盖全部 84 个 3-多重集，0 类不完整）。
- 结论：k=3 严格不可行；**全队目标已是锁定 k=4**。k=4 复核三件套（`fastcov.py`、`resid_check.py`、`structural_k4.py`、`verify_strategy.py`）+ k=4 两个已知坑（chiitoi 需 ≤5 组鸽笼 + z 标记码 (z,a,a,b)；分配按 p₄(μ) 容量）见 §3.4。

## 4. 后续接手步骤

1. 先确认口径：strict 天凤七对子（否则数字全变：loose 下清一色 47,933/408、全局 15,592）。
2. 拿到新 plan 后先跑 `python -u work/verify/gap_exact.py <plan>`（≈5 分钟）——它给出精确缺口清单；再跑 `verify_strategy.py 1000000 <plan>` 出完整报告。
3. 判定标准（必须全部通过）：(a) 类集 == `census_strict.json`（2846）；(b) 有序码全局唯一 + 多重集复用 ≤ p(m)；(c) 每类至少 1 码；(d) Type I 块 DFS 0 uncovered；(e) 全部单类别手牌 0 uncovered 且反向解码一致；(f) chiitoi 0 缺口；(g) 国士 ✓；(h) 10⁶ 手模拟 0 失败。
4. 若 k=3 继续不收敛：k=4 的预算（每门 9⁴=6561、全局 34⁴=1,336,336）远超需求（清一色 Στ 级数 ≤565），k=4 几乎必然可行；报告应写「k∈{3,4}，k=3 未验证 / k=4 可行」，不要写成「答案 = 3」。
5. 复现命令全部列在 `VERIFY.md` §5。

## 6. 收工交班总结（2026-09-16，按 lead 要求）

### 6.1 已就绪的工具清单与用法（全部在 work/verify/）

| 工具 | 用法 | 作用 / 速度 |
|---|---|---|
| verify_k3_disproof.py | python -u work/verify/verify_k3_disproof.py | **k=3 否证独立重放**：U={m2..m8} → 7,875 向量 / 5,628 听牌手 / N=347 / L=52 / 399>343；逐条校验 52 个 L 类的 blocker（覆盖全部 84 个 3-多重集）。约 1 分钟 |
| structural_k3.py / structural_k4.py | python -u work/verify/structural_k4.py <plan> | 类集==2846 / 0 空类 / 有序码全局唯一（⇒decode 良定义）/ 每码 ⊆ 该类某手牌（单花色类全量）/ 独立 W 抽查。约 10 秒 |
| fastcov.py | python -u work/verify/fastcov.py <plan> | 四花色单门手牌**全量**覆盖（numpy 向量化 + W 缓存）+ 逐类 all_failures。**0.6 秒/轮** |
| resid_check.py | python -u work/verify/resid_check.py <plan> | (a) Type I 块级 DFS 覆盖 (b) chiitoi 20 万抽样 (c) 30 万结构化模拟。约 13 分钟 |
| verify_strategy.py | python -u work/verify/verify_strategy.py 1000000 <plan> | 全量版：结构 + Type I + 子宇宙 + chiitoi + 国士 + 10^6 手 + 反向解码（计数不截断：typeI_uncovered_n / chiitoi_fail_n）。约 13 分钟 |
| chk_chiitoi.py | python -u work/verify/chk_chiitoi.py <plan> | **精确**判定 97 个 chiitoi 描述子（61 类）是否全覆盖（超图独立 6-集搜索）+ (z,a,a,b) 容量饱和统计。约 1 分钟 |
| waste_perm.py | 改脚本内 plan 路径后运行 | 统计空排列槽（多少多重集仍有未用排列） |
| dump_gap_hands.py | python -u work/verify/dump_gap_hands.py <plan> 3p,7p | 导出指定单花色类的未覆盖手牌 + 该类码（秒级） |
| refit_local_k4.py / permfix_k4.py / fastfix_k4.py / repair_k4.py | 见脚本头 | k=4 生成/修复实验（后备路径）：破容量墙 / 排列回退+通用码优先 / 命中集补码 |
| 缓存 cache_w_{m,p,s,z}.npz + .json | 自动生成 | 单门手牌 W 缓存（首次约 35 秒/门，之后全量复验秒级）；定义若变须加 --rebuild |

### 6.2 今日已确认的结论

1. **k=3 否证成立（verifier 独立重放通过）**：U={m2..m8}（7 张），N=347、L=52、下界 **399 > 343 = 7^3** ⇒ k=3 不可行，**k_min ≥ 4**。347 个类集合与 52 个 L 类集合与证书逐一相等；52 类 blocker 逐条有效且完备。
2. **k=4 plan_k4_v2.json（designer 换码版）复核**：
   - (a) Type I 未覆盖块 = **47**（与 designer 自报一致；permfix 底版 155）
   - (b) chiitoi 20 万抽样失败 = **73**（designer 自报 3,926 是另一口径）；**精确描述子判定：97 个中 77 个失败，涉及 41 个类**
   - (c) 30 万结构化模拟失败 = **8,301**（10^6 手版未跑完，属同一问题更大样本）
   - (d) 结构：类集 2846 ✓ / 0 空类 ✓ / 411,541 条有序码**全部唯一** ✓ / 每多重集用量 ≤ p4 ✓ / 独立 W 抽查 0 失配 ✓ / **但有 33 条码 ⊄ 该类任何手牌** ✗（全是要求 3~4 张该类单骑牌的废码，如类 {9m} 的 (9m,9m,9m,9m)）；fastcov 四花色单门覆盖 0/0/0/0 ✓
3. **chiitoi 残余澄清**：残缺点全部落在 61 个含描述子的类内 ✓；原因**不只是容量饱和**——5,444 个 (z,a,a,b) 多重集中 2,907 个 12/12 饱和、**2,537 个仍有余量** ⇒ 主因是**配对族不完整**（需 α≤5 的 93 对设计；当前漏掉如 W={1m,4m,7m},z=7m 的 K={1m,8m,9m,1p,2p,3p} 这类每组各取一张的 6 集）。

### 6.3 明天第一件事

对 work/strategy/out/plan_k4_v3.json（analyst 在做：chiitoi 换不同 5 组划分 + 二级链式换码）跑全套：

    python -u work/verify/structural_k4.py work/strategy/out/plan_k4_v3.json
    python -u work/verify/fastcov.py        work/strategy/out/plan_k4_v3.json
    python -u work/verify/chk_chiitoi.py    work/strategy/out/plan_k4_v3.json
    python -u work/verify/resid_check.py    work/strategy/out/plan_k4_v3.json
    python -u work/verify/verify_strategy.py 1000000 work/strategy/out/plan_k4_v3.json

**验收线**：Type I 未覆盖 = 0、chiitoi 抽样失败 = 0、10^6 手模拟失败 = 0；结构四项全过且**无废码**（每码 ⊆ 该类某手牌）。

### 6.4 脚本已知坑（务必先读）

1. resid_check.py 的 (a) **只覆盖 kind I 来源**；kind II 块只能靠 (c) 模拟 / verify_strategy 间接覆盖 —— 精确覆盖 kind II 需要 per-A 表 work/recon/table_perA.pkl。
2. resid_check.py 的 (b) 是**抽样**（20 万手）；精确判定请用 chk_chiitoi.py（超图搜索，无抽样）。
3. 别再看旧日志计数：早先 typeI_uncovered / chiitoi_fail_examples 有 [:5] 截断（恒显示 5），已修为 typeI_uncovered_n / chiitoi_fail_n。
4. 缓存 cache_w_*.npz 是加速基础；若 compute_W 或口径改变必须 --rebuild，否则结果不一致。
5. 单花色完备性检查只覆盖「全部落在某一门」的手牌；跨门手牌依赖模拟/DFS，报告里必须区分「完备」与「抽样」。
6. 历史判据坑：字牌类别**不能有顺子**；Type II 雀头类必须 melds_pair(X) 而非「有对子」；严格七对子听牌 = sum(x==2)==6 and sum(x==1)==1；加所听牌必须查 4 张上限。

## 5. 需要 Lead / 其他人配合

- **designer / lead**：终态 plan 必须满足 (b)(c) 两条硬约束（每类非空 + 有序码唯一/容量不超），并给出 decode 表；写完 ping verifier 跑 §4.2。
- **enum-core / analyst-lower**：若继续用 MODEL.md 的结构判据，请先按 §3.1 的 2、3、4 三条修正（字牌无顺子、melds_pair、严格七对子），否则全局类表会多/少类。
- **Lead**：REPORT.md 里 k=3 必须标注「未验证」；若采用 loose 口径请明确写出规则出处（天凤实际是 strict）。

## 7. 最终验收（k=4 已通过，2026-09-17）

**结论：k_min = 4 完整成立。** 下界 k=3 不可行（work/lowerbound/k3_disproof_certificate.json，独立重放 work/verify/verify_k3_disproof.py：U={m2..m8}, N(U)=347, L(U)=52, 399 > 343）；上界由显式方案给出：

- 终态文件：**work/verify/plan_k4_FINAL.json**（2846 类 / **17,579** 条有序 4-码）
- **sha256 = b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163**
- 机器可读证书：work/verify/final_certificate.json；哈希副本 plan_k4_FINAL.sha256

承接链（可追溯）：plan_k4_final（无效，仅作病史）→ plan_k4_zero（诊断）→ **leadC sha256 4e36492e…（17,527）** → 补 55 条（|A|=4 硬块各补 A 的一个排列，patch_leadC2.py）→ 17,582 → 删 3 条不合法码（finalize_final_plan.py）→ **17,579 = FINAL**。

### 7.1 验收表（全部为 0 残差，命令见 7.3）

| 判据 | 工具 | 数字 |
|---|---|---|
| 类集合 = 独立普查 | structural_k4 / fastverify | 2846/2846，0 空类，duplicate W rows 0 |
| 条件1 S_C ⊆ ∪_{H∈C}M_k(H) | waste_exact.py | 17,579 码 → **0 浪费**（200 抽样复核 0 误报） |
| 条件3 各类码集两两不交 | structural_k4 | 17,579 distinct ordered = 17,579 ⇒ 全局唯一 |
| 条件2（I 块，精确 DFS） | block_coverage_exact.py | 168,817 基式 → **未覆盖 0** |
| 条件2（II 块，精确 DFS） | block_coverage_exact.py | 5,402,697 基式对 → **未覆盖 0** |
| 条件2（逐类抽样，30/120 手） | perclass_coverage.py | 2846 类 → 完全无覆盖 0 / 部分 0 |
| Type I 块（fastverify 口径） | fastverify_k4.py | 166,746 块 → **0 未覆盖** |
| chiitoi 97 描述子 | fastverify_k4.py | 97 → **0 失败** |
| 国士（13 面 + 13×12 缺一张） | perclass_coverage.py | 全族手牌覆盖，0 失败 |
| 单花色码完备核 | structural_k4 | 4,358 码 → 0 bad |
| 单花色块 | fastverify_k4 | 未覆盖手牌 0 |
| 10⁶ 手模拟（两条独立实现） | fastverify_k4 / sim_fail_detail | 听牌 366,941 / 366,249 → **失败 0 / 0** |
| W 独立抽查 | structural_k4（compute_W） | 1,600 手 → 0 失配 |

**交叉验证（第三套独立实现）**：analyst 的 `verify_k4_plan.py` 已独立复跑 FINAL 八项全 0 —— work/lowerbound/verify_k4_FINAL.json：check1 类集相等 symdiff 0；check2 空类 0；check3 码碰撞 0 / 超容量 0（max_use 18 ≤ 24）；check4 条件1 未证实 **0/17,579**；check5 单元 5,571,671 → **未覆盖 0**；check6 chiitoi 97 描述子 → 0 失败；check7 国士 0；check8 10⁶ 手（听牌 384,418）→ 0 失败；VERDICT_k4_plan_ok = true。其 plan 路径与 17,579 码数同本文 sha256 **b95f5523…** 一致。

### 7.2 本轮验证新增的三条判据（此前缺失）

1. **逐类"同类覆盖"（MODEL.md 条件2）**：旧工具只统计"码表非空"，因此 plan_k4_final 上 137 类全无覆盖 + 849 类部分无覆盖被漏掉。工具：perclass_coverage.py。
2. **I+II 两种块的精确 DFS 覆盖**：fastverify 的 typeI（其 line 67）只装配 kind I；II 块此前无人核。工具：block_coverage_exact.py（遍历 PROFI_D/PROFII_D 全部 A 变体 × inert 类别面子补全，带早停与见证手牌）。
3. **条件1 的精确判定修正**：waste_exact.py 的 KOK 分支原先保守地"一律视为可用"，漏掉 14 条（13 幺九类）证明性浪费码；已按类重建 KOK 手牌族（|W|=13：1 手；|W|=1：12 手，均用 indep_core.compute_W 独立验证 W 恰为该类）。分析师清单 work/lowerbound/waste_list.json（5,249）与此差异 7 条，全部在"13 幺九"类，根因是 k4_sources.py 的 KOK_HANDS 全局池化（line 59-66/105-106）。

### 7.3 复跑命令（约 4 分钟，12 进程）

    python -u work/verify/block_coverage_exact.py work/verify/plan_k4_FINAL.json
    python -u work/verify/waste_exact.py work/verify/plan_k4_FINAL.json waste_list_FINAL.json
    python -u work/verify/perclass_coverage.py work/verify/plan_k4_FINAL.json 120
    python -u work/verify/fastverify_k4.py work/verify/plan_k4_FINAL.json 1000000
    python -u work/verify/structural_k4.py work/verify/plan_k4_FINAL.json
    python -u work/verify/sim_fail_detail.py work/verify/plan_k4_FINAL.json 1000000

注意：block_coverage_exact.py / perclass_coverage.py 的参数是 <plan.json>，autograder 口径见各脚本 docstring；旧脚本 structural_k4.py **必须带 plan 路径**，否则 fallback 到已删除的 work/recon/plan_k4_lead_plan.json。

## 8. task-11 / L2：Lean 子宇宙预算引理（已通过，详见 work/verify/LEAN_L2.md）

产物 `lean/Mj/Lemma.lean`（sha256 840fea20f62de0b2…）：`seqU/codesU` + `mem_codesU`/`codesU_nodup`/`codesU_length` + `budget` + `classes_le_pow` + `no_common_code_two` + `contains_eq_true_iff`。

- **两处题面语句修正（反例均机器验证，lean/Counterexample.lean，exit 0）**：
  1. `budget` 缺 `hcls : cls.Nodup` 与 `hSnodup : ∀ S ∈ cls, S.Nodup`：反例 `U=[t0], k=1, cls=[[[t0],[t0]]]`（hdisj 真空）⇒ sum=2 > 1；重复类 `[[[t0]],[[t0]]]` 同样失败。
  2. 推论② 缺 `hS : ∀ c ∈ S, c.length = k ∧ ∀ t ∈ c, t ∈ U`：反例 `k=0,U=[t0],Hs=[[[t0]]],S=[[t0]]` ⇒ hHsne/hcover/hno 全 ✓ 但 `S.length = 1`。
- **集成**：`lean/Mj.lean` 由 verifier 加 1 行 `import Mj.Lemma`（否则 `lake build` 默认目标不构建本文件）；加后整库 6 jobs 全绿。
- **验收**：`lake build` = 6 jobs 成功；`lake build Mj.Lemma` 成功；`#print axioms` → budget/classes_le_pow: [propext, Classical.choice, Quot.sound]；no_common_code_two / contains_eq_true_iff: [propext, Quot.sound]；无 axiom/sorry/admit/native_decide（另见 work/verify/check_lean_lemma.py 静态扫描）。
- 复跑：`cd lean; lake build; lake env lean Mj/Lemma.lean`；静态：`python -u work/verify/check_lean_lemma.py`。
- 共享写域：`lean/Mj/Basic.lean` 未被改动；`lean/Mj/Disproof.lean` 本轮被**其他队友**改动（非 verifier），当前整库仍全绿。


