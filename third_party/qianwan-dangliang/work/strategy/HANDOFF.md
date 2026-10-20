# HANDOFF — T4（designer-encoder, work/strategy/）

## 1. 状态

- **已完成**：
  - 严格七对子口径（7 个不同牌种的对子）的**独立类表**：**2,846 类**。
    与 enum-core `work/data/out/global.json` 的 W 集合**对称差 = 0**（`cross_global.py`）。
  - 类 → **来源块**结构（Type I / Type II / tanki / 国士 / 纯七对子）与"通用码"判据，逐类见证验证（真实手牌 `waits13`），**2846/2846 全部通过**。
  - **不加容量约束**的覆盖：Σ|S_C| = **22,284**（2,846 类全覆盖，含 34 个单元素类的 tanki/chiitoi 保留码族）。
  - 子宇宙预算独立复核：m 宇宙 Στ_m = **581 ≤ 729**、z 宇宙 Στ_z = **42 ≤ 343**（贪心上界，τ=1/2 精确）；
    另：单花色 13 张多重集数 **93,600** 已用容斥确认（lead 的 93,516 差 84）。
  - 自检器 `check.py`（对**任意** plan.json 可用）。
- **未完成**：**k=3 的全局不相交装包**。当前 `out/plan.json`（5490 有序码）**不是合法终态**：
  - 有序码 0 冲突 ✓、多重集容量 0 违例 ✓（verifier 已确认这两条合格）；
  - 但 **995 个类没有任何码**，且 2,213 个来源元素未被覆盖；
  - check.py 在 1,040,210 手模拟中：清一色 40,196 手失败 31,742、随机标准型 600,000 手失败 146,038、
    随机七对子 400,000 手失败 10、国士 14 手失败 0。
- 最后一条可用命令（约 18 分钟，产出 out/check.json）：
  ```
  $env:PYTHONIOENCODING='utf-8'; python -u work/strategy/check.py
  ```
  构造（约 90 秒，元素缓存命中时）：`python -u work/strategy/strategy.py`

## 2. 交付物清单

| 文件 | 说明 |
|---|---|
| `work/strategy/mjlib.py` | 牌模型、和牌判定、**严格口径** waits13 |
| `work/strategy/table_lib.py` | 严格口径类表 + 来源块（kind/key/mode/z/cap/nsrc）；`build()` 返回 cls/PROFI_D/PROFII_D/fam_list |
| `work/strategy/strategy.py` | encode/decode 框架 + 构造器（元素化覆盖 + 两阶段装包） |
| `work/strategy/check.py` → `out/check.json` | 自检：结构化全称判据 + tanki 族 DFS + 有序码唯一 + 子宇宙预算 + ≥10⁶ 手模拟 |
| `work/strategy/STRATEGY.md` | 策略与判据说明（含未完成原因） |
| `work/strategy/out/plan.json`, `out/decode.tsv` | 当前 **WIP/不合法** 的构造产物 |
| `work/strategy/out/elements.pkl` | 每类来源元素 + 候选码缓存（重建需 ~4 分钟） |
| `work/strategy/cross_global.py` | 与 enum-core global.json 类集对拍（对称差 0） |
| `work/strategy/verify_table.py` | 类表见证验证（用真实手牌对拍每个类） |
| `work/strategy/universe_budget.py` → `out/universe_budget.json` | 子宇宙 Στ（m、z），严格口径 |
| `work/strategy/flush_lab.py`, `check_indep.py`, `census.py`, `diff_typeI.py` | 清一色/普查的过程脚本（含 recon bug 证据） |

## 3. 已知 bug / 未收敛原因（核心）

**已发现并修正的 bug（影响过别的队友）**
1. `work/recon/recon_flush.py` 的 `gen_run_vecs` 每个起始位置只允许一条顺子 ⇒ 漏"重复顺子"，
   清一色真值应为 4 面子多重集 2098（recon 1143）、听牌 40,070（recon 26,680）、类 387（recon 383）；
   MODEL §6 旧值作废。
2. `work/recon/recon_global2.py` Type II 把两个**局部** bitmask 合并再移位解码（`V1|V2` 后 `>>ncat(c1)`），
   W 完全错；931 类/9164 类的旧结论随之作废。**请勿再用该脚本。**
3. 我自己的 `x_profile` 曾把 Wp/V 的牌号**双重偏移**（局部 t 又被加 CAT_BASE），产生幻类；已修。
4. 国士 KOK12 块曾把"和牌"当成"听牌"存进类表（|W|=12 的 13 个幻类）；已修（枚举 156 手国士听牌 + waits13 定类）。
5. `check.py` 的若干 key/类型 bug（"S" 元素向量下标、JSON list 不可哈希）；已修。

**k=3 装包未收敛的真实卡点（请接手者重点看）**
- 码 = **有序** 3 元组；同一多重集 m 能服务的类数上限 = p(m) = 3!/∏重数! ∈ {1,3,6}。
- 不加重叠约束的贪婪覆盖 Σ = 22,284，但**需求集中在少量高覆盖码**（如 {2m,2m,2m}，p=1，被 900+ 类需要）。
- 加"硬阻塞已满多重集"后，贪婪只能改用低覆盖码 ⇒ 单类覆盖码数变大 ⇒ 需求更大（雪崩）：
  实测 Σ 膨胀到 47,041（阶段2 内部 0 超容量但最终 560 个多重集超容量）与 98,516（579 超容量、995 空码类）。
- 试过但失败的修法：使用率惩罚（λ=2，Σ=43k，仍集中）、逐多重集驱逐（太慢，未收敛）、
  类级 cap 快捷码（大多数类的**类级** cap=0，只有 1 类命中——因为 cap 是"全部块"的交，单类别类的 m-only 块 cap 才有用）。
- 本质：这是一个**带容量的集合覆盖/装包**问题，正确的解法需要全局匹配/流，而不是逐类贪婪。

## 4. 后续接手步骤（建议顺序）

1. **先确认口径**：所有数字用严格七对子（`mjlib.waits13`）；类数 2,846。
2. **k=3 装包重写（首选）**：候选优先限制为"**三张不同牌**"的码（p=6；池 = C(34,3)=5984 个多重集 × 6 = 35,904 个有序码，
   足够 22k 需求）；对每类先取"块级 cap 3 子集"最优码，再用**类间换码（Kuhn 增广/Hall）**消解冲突，
   禁止"单类补码"；或直接写成 ILP（每类至少要覆盖其元素，每多重集用量 ≤ p(m)）。
3. **k=4 退路（几乎必然成功）**：预算 34^4 = 1,336,336；每多重集 p4(m) ∈ {1,4,12,24}；
   清一色 9^4 = 6,561 ≫ Στ_m(387 类 ≤ 565~676)。建议直接做一份 k=4 终态 plan 作为**可发布上界**：
   `strategy.py` 的 `K` 与 `ksubs` 可按 K 参数化；tanki 族换 {(x,a,a,a)} ∪ {(x,a,b,c)}；
   纯七对子换 (z,a,a,b) 边族（33 种牌分 5 组组内连边 = 93 条即可命中任意 6 对）。
4. **验收**：任何终态 plan 跑 `check.py`（结构化 + 1e6 手）+ verifier 的 `work/verify/verify_strategy.py` 双跑。
5. **期望数字**：无容量约束 Σ|S_C| ≈ 22k（2,846 类）；k=3 若可行 Σ 应 ≤ 39,304 且 m/p/s 各 ≤ 729；
   k=4 时 Σ 应远小于 1.34M。

## 5. 需要 Lead/其他人配合

- **plan 格式统一**：建议终态 plan 统一成
  `{"k":3,"plan":[{"W":[牌号...],"codes":[[c1,c2,c3],...]}]}`（我的 `check.py` 与 verifier 的验证器都吃这个格式；
  lead_plan_k3.json 目前是牌名 + Wmask，需要一次转换）。
- **分配器分工**：我可以继续做 k=3 的匹配/ILP 版装包，或转做 k=4 终态；请 lead 指定优先级。
- **文档**：STRATEGY.md/本 HANDOFF 里的"未完成"标注请保留到真正有合法终态为止，避免误报 k=3 成立。

---

## 8. 追加（k=4 续做轮，最新状态）

**目标**：锁定"答案 ≤ 4"的硬上界。

**已实现（strategy.py 已参数化）**
- \`STRAT_K=4\`：码 = 有序 4 元组；多重集容量 p4(m) = 4!/∏重数! ∈ {1,4,6,12,24}；输出 \`out/plan_k4.json\` / \`out/decode_k4.tsv\`。
- tanki 族（k=4）：\`{(x,a,a,a)} ∪ {(x,a,a+1,a+2)}\`（每个补牌族 F 含一个面子 ⇒ 刻子/顺子各被命中）。
- 纯七对子族（k=4）：\`(z,a,a,b)\` 的 2-子集族 —— 33 种牌分 5 组(7,7,7,6,6)、组内连边（93 条）⇒ 任意 6 对必含一条边。
- **阶段 0 固定分配**：\`LEAD_COVERS=a;b\` 可把 lead 的 \`work/recon/k4_subuniverse_covers.json\`（1189 类/本门码）+ \`work/recon/k4_cross_covers.json\`（75 类）**固定**进 plan，其余类在剩余容量内装包。
- **阶段 3 驱逐修复**：按真实覆盖重算"每个多重集的使用次数"，把超容量/空码类逐类重排，并可驱逐其它类的一个占用者腾容量；目标是精确满足"使用次数 ≤ p(m)"（这样 make_tables 不会再丢码 ⇒ 无空码类）。
- 覆盖类 \`cover_with(W, blocked)\`：分"单门元素 / 跨门元素"两段贪心，只有**逐元素全覆盖**才接受（失败返回未覆盖集合）。

**当前产物与硬指标（\`out/plan_k4.json\`，即 verifier 说的 18:02 版）**
- 2846 类 ✓（类集与 verifier 独立类集一致）；13,069 条有序码**全部不同（0 复用）** ✓；**多重集 0 超容量** ✓；
- **但 422 个类没有任何码** ✗（make_tables 在"排列耗尽"时丢码所致）⇒ 仍不是合法终态。

**未收敛的原因（精确定位）**
1. 我的分配是**逐 A 通用码**（每个来源元素一条可覆盖它的码），对 minA<4 的块会产生大量码需求（lead 实测去重后 A 需求 5.57M）→ 与多重集容量 p(m) 冲突；
2. 阶段 3 的驱逐修复虽然原理正确，但**太慢**（每轮对上千个类做候选×占用者搜索），单轮 >20 分钟未收敛（已杀掉），需要：
   - 先做**块级锚牌族覆盖**：块内所有 A 若有公共牌 x，直接用 \`{(x,a,a,a)} ∪ {(x,a,b,c)}\`（~48 条，码长恒 4）覆盖整块；只有"无公共锚牌"的块才逐 A。
   - 阶段 3 只对**超容量多重集涉及的类**做修复（不要全量重排），并且用"先修小类、后修大类"的顺序。
   - 或者直接改用**流/匹配模型**：类 × 多重集（容量 p(m)）的二部 b-匹配 + 覆盖约束，比逐类贪婪稳。
3. 另一条已知可行路径（lead 已备料）：\`k4_subuniverse_covers.json\`（1189 类，0 未覆盖块）+ \`k4_cross_covers.json\`（75 类）已把"必须本门码"的类全部覆盖；只要把**其余 1582 个跨门类**在剩余容量内装完（它们的 minA 大多 ≥4，可一条码覆盖整块），即可一次性通过。

**接手最短路径（建议）**
1. \`STRAT_K=4 LEAD_COVERS="work/recon/k4_subuniverse_covers.json;work/recon/k4_cross_covers.json" python -u work/strategy/strategy.py\`
   —— 先看阶段 3 是否能收敛；不收敛就按上面 2/3 优化。
2. 终态检查：
   \`PLAN=work/strategy/out/plan_k4.json python -u work/strategy/check.py\`（结构化 + ≥10⁶ 手，写 \`out/check_k4.json\`）
   \`python -u work/verify/k4_gap_classes.py work/strategy/out/plan_k4.json\`（verifier 的缺口表）
   \`python -u work/verify/verify_strategy.py 1000000 work/strategy/out/plan_k4.json\`（verifier 终验）
3. 通过后锁定"答案 ≤ 4"，再回头攻 k=3。

**注意**：\`out/plan_k4.json\` 目前**不是终态**（422 空码类），请勿作为"k=4 可行"的证据。

---

## 9. 终态与独立交叉验证（本轮收口）

**团队终态产物**：`work/verify/plan_k4_FINAL.json`（k=4，2,846 类；答案 = 4 已定）。

**我的独立 check.py 对同族基线 `work/verify/plan_k4_leadC_patched.json` 的结果**（`PLAN=... python -u work/strategy/check.py` → `out/check_k4.json`）：

| 检查项 | 结果 |
|---|---|
| 类数 / 有序码 / 冲突 / 缺类 | 2,846 / 17,582 / **0 冲突** / **0 缺类** ✓ |
| **手牌级模拟（合计 1,040,210 手）** | **全部 0 失败** ✓：清一色全量 40,196、随机标准型 600,000、随机七对子 400,000、国士 14 |
| 子宇宙预算（k=4） | m: Στ_U = **691 ≤ 6,561** ✓；z: **42 ≤ 2,401** ✓ |
| 结构化逐单元判据 | 1,075,236 单元中 **1,717 未命中** ⚠️ |

**关于那 1,717 条**（残留不确定性，如实记录）：
- 失败样例全部是**单元素类**（W={1m},{2m},… 的 `A` 类单元），且**手牌级 1.04M 模拟 0 失败**、verifier 的 `block_coverage_exact` 在打补丁后也归零 ⇒ 高度疑似**我的"单元→类"抽象过宽（假阳性）**：这些元素来自某些块的 side/am 变体，其对应的手牌组合未必都属于该类。
- 结论：以 verifier 的逐块 DFS（block_coverage_exact）+ 双方手牌级模拟为准；我的结构化线可作为"疑似缺口"的探针，若要闭环需按来源变体逐一核对（未完成，留给后续）。

**其它交付（本轮）**：
- `FASTPACK.md` + `fastpack.py` + `out/table_cache.pkl`：建表 cold 18.4 s → cached **0.50 s（≈37×）**；Pool(12) 逐类覆盖 104.3 s → 72.8 s（1.43×，逐类结果 identical）。
- `out/replace_candidates.json` + `replace_stats.json`：1,822 个饱和 μ / 21,145 条占用者 / 可替换比例 3.2% / blocked 20,473（含单元 X），供换码与链式增广。
- `K3.md`（k=3 被否证留档）、`K4.md`（已标注被终态取代）、`fix_k4.py`/`fix_k4b.py`/`chiit_fix*.py`/`fix30.py`（各轮修复与实验）。
