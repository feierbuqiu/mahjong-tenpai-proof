# k=4 修复交接（work/strategy/out/）

> 作者：analyst-lower（临时接手 designer-encoder 的 k=4 plan 收尾）

## 1. 现状（截至本轮结束）

| 文件 | 状态 |
|---|---|
| `plan_k4_v2.json` | **唯一有效 plan**。2,846 类 / 411,541 有序码（全不同）/ 0 空类 / 0 超容量 / 最大用量 24 |
| `plan_k4_v2.json` 残余 | **Type I 未覆盖 47 块**；**chiitoi 缺 3,926 个族码** |
| `plan_k4_v3_aborted_chi_only.json` | 我这一轮的失败尝试（chiitoi 只修好 0/78）。**不要使用**，它只是在饱和多重集上多占了容量 |
| `fix_chi_v3_report.json` | 该尝试的报告（含 78 个失败 (W,z) 的样本） |

## 2. 我新增的脚本

| 脚本 | 用途 | 备注 |
|---|---|---|
| `fix_chi_v3.py` | 轻量 chiitoi 修复（不加载 table_lib，14 秒） | 已证明"换划分"不够；可作后续实验骨架 |
| `repair_v3.py` | 完整版：chiitoi 换划分 + 链式换码 + Type I 链式换码 | **卡在 `table_lib.build()`**，需后台跑并给足时间 |
| `resid_v3.py` | 复现残余（Type I 用 fam_list 全量判据） | 全量枚举较慢（>10 分钟） |
| `diag_chi.py` / `diag_chi2.py` | chiitoi 饱和分布与 K6 障碍诊断 | **结论见 §3** |
| `inspect_plan.py` / `peek_src.py` | plan 与 global.json 的结构探查 | — |

## 3. 本轮最重要的发现：chiitoi 残余不是"族设计"问题

- 对每个 (类 W, z)：七对子手牌 H = z + 2K（K 是 6 张对牌）。
  一条码 (z,a,a,b) 命中 H ⟺ {a,b} ⊆ K。所以要求：33 张非 z 牌的图上，已分配对集的独立数 α ≤ 5。
- verifier 与我都观察到容量层面有缺口，但真正的障碍是：
  **`diag_chi2.py` 对全部 97 个 (W,z) 都找到了"饱和 K6"**——存在 6 张非 z 牌，其 C(6,2)=15 个对对应的多重集
  `(z,a,a,b)` **全部已满**（usage = 12/12，例：z=3m 时 528 对中 246 对饱和）。
  ⇒ 该 6 集 K 对应的手牌在当前 plan 下**没有任何 (z,a,a,b) 码可命中**，且换划分不可能解决。
- 两条出路：
  1. **换容量**：用链式换码把占据饱和 `(z,a,a,b)` 的其它类的码挪到别处
     （需要 table_lib 的 `units(W)` 与 `am_of(W,mu)`；判据 nu ⊆ am'(C',mu) 保证被挪的类不丢覆盖）；
  2. **换形状**：手牌 H = z + 2K 里还有 12 张对牌可用，因此
     `(z,a,b,c)`、`(a,a,b,c)`、`(a,a,b,b)`（a,b,c ∈ K）同样能命中。
     把"每个 6 集 K 必被某条已分配码命中"直接当覆盖判据做贪心，可能比"93 对族"更省容量。

## 4. 建议的下一步（按顺序）

1. 跑 `python -u work/strategy/out/diag_chi2.py` 复核 K6 结论（秒级）。
2. 实施 §3 的路线 2（换形状）：对 97 个 (W,z) 贪心加码，判据是"K 被覆盖"，
   每次选**当前未饱和**的多重集；若某 (W,z) 仍失败再走路线 1。
3. Type I 47 块：用 `repair_v3.py` 的链式换码（深度 ≤3，访问集合防环），
   但要在后台跑（`table_lib.build()` 与 fam_list 全量枚举都慢），建议 `--time-budget 3600`。
4. 每步之后都要落盘并重算残余；验收线 **Type I = 0 且 chiitoi = 0**。
5. 然后交 verifier：`python -u work/verify/resid_check.py <plan>`、`work/verify/fastcov.py`、10⁶ 手模拟。

## 5. 注意事项
- plan 的 schema 必须与 v2 一致：`{"k":4,"n_classes":...,"n_codes":...,"plan":[{"W":[...],"codes":[[...]]}]}`。
  （designer 的 `check.py` 还需要每类的 `modes`/`reserved` 字段，v2 里没有，故 `check.py` 不能直接跑在 v2/v3 上。）
- 码的唯一性是**有序码**级别：同一多重集 mu 最多可服务 `p4(mu) = 24/∏重数!` 个类（4 张全不同 → 24；(2,1,1) → 12；(2,2) → 6；(3,1) → 4；(4) → 1）。
- 千万不要为了让某个类"看起来被覆盖"而重复分配同一条有序码——那会让 decode 失效。
