# WASTE.md — 无效码删除的安全性论证（k=4 plan）

## 结论
`work/lowerbound/waste_list.json` 列出 **5,249 条**"不 ⊆ 本类任何手牌"的码（350 个类）。
这批码可以安全删除：**删除不改变任何类的覆盖性**，只会释放多重集容量（chiitoi/Type I 修复正需要）。

## 安全性论证
1. 协议要求：对每个类 C 和每手 H ∈ C，存在被分配的码 c ∈ S_C 且 **c ⊆ H**（A 才能把 c 摆到 B 要翻的位置上）。覆盖性只依赖"码 ⊆ 手牌"。
2. `waste_list.json` 中每条 c 都满足：**类 C 的任何一手牌都不含 c**。故 c 对 C 的覆盖无任何贡献，删掉后 C 中每手牌的可用码集合不变。
3. 删除只减少 S_C 的元素，不会引入新冲突（有序码唯一性只会更易满足），也不影响其它类。⇒ 覆盖性与 decode 正确性不变。

## 判定方法（精确，非保守近似）
- 来源块：`work/recon/table_perA.pkl` 的 `cls`（每类 → I/II/KOK 块，带 profile key）
- A 变体表：同文件的 `PROFI_D` / `PROFII_D`（(类别,尺寸,profile) → **(am, xs)**，xs 是该 profile 下**全部** A 变体）
- 判据：c ⊆ 某手牌 A⊎F ⟺ (a) c 在主动类别的部分 ⊆ **某个** A 变体（逐一遍历 xs，不用 minA）；(b) 其余牌可塞进 j 个惰性面子（min_parts(R) ≤ j）；(c) 或 ⊆ 国士手牌；或符合该类 chiitoi 形状（6 对 + 单张 z）。
- 前提：来源清单完备（T2 普查 + verifier 复核）。

## 与早先数字的差异（重要）
早先第 ④ 项报 **87,734**，其中 **82,485 条是误报**（94%）：当时 kind II 缺 A 变体表，只能用 minA1+minA2 保守判据，
把"只适配非 min 变体"的**可用码**误判为浪费（verifier 抽样审计的误报例：类 {1m} 的 (1m,3p,3p,6p) 其实可用）。
接上 `table_perA.pkl` 后精确重算 = **5,249**。**不得按 87,734 删码。**

## 抽样证据（防误删）
`work/lowerbound/waste_sample_evidence.json`：随机 200 条待删码，逐条列出该类全部来源块的判定明细
（类别/尺寸/A 变体数/j/min_parts(rest)/是否通过）与 chiitoi 描述子；200/200 复核仍"不可用"，**反例 0**。

## 复现
    python -u work/lowerbound/export_waste_exact.py          # 约 20 秒, 生成 waste_list.json + 抽样证据
    python -u work/lowerbound/verify_k4_plan.py <plan> --sim 1000000   # 第④项已改为同一精确判据

## 交叉对拍状态
- verifier 的 `work/verify/waste_list_exact.json` 目前**写到第 6 行截断**（记录 waste_count = 22,401），尚不可 diff。
- 与其 `waste_codes_report.json` 公布的 5 个"疑似不可用"例子对拍：**全部不在**我的精确清单里（确实可用，属保守判据误报）✓ 方向一致。
- **建议**：verifier 用同一份 `table_perA.pkl` + "全 A 变体"判据重跑，两边做集合对称差；**对称差为 0 才执行删除**。
