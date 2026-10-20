# FASTPACK.md — 并行化与加速记录（designer-encoder, work/strategy/）

机器：i5-10600K，6 物理核 / 12 逻辑核，Python 3.14，numpy 2.5.2。

## 1. table 缓存（\`fastpack.load_table\`）

| 模式 | 耗时 |
|---|---|
| 首次 cold：\`table_lib.build()\` + pickle 落盘 \`out/table_cache.pkl\` | **18.4 s**（另一次实测 27.2 s，随机器负载波动） |
| 之后 cached：\`pickle.load\` | **0.50 s** |

⇒ **约 37× 加速**，所有后续脚本（pack/fix/replace/fastpack）都可直接 load，省掉每次 18–27 s 的重算。
用法：\`T, mode, dt = fastpack.load_table()\`（\`mode ∈ {cold, cached}\`）。

## 2. 逐类覆盖：Pool(12) 并行

基准：随机取排序前 300 个类，跑同一 \`cover_units_np\` 贪心（numpy 广播判"码 ⊆ 单元"）。

| 版本 | 300 类覆盖耗时 | 结果一致 | Σ码 |
|---|---|---|---|
| 串行 | 104.3 s | — | 1296 |
| \`multiprocessing.Pool(12)\`（按"块数"贪心均衡分片；worker 用 initializer 各自 pickle.load 缓存表） | **72.8 s** | ✅ 逐类码集完全相同 | 1296 |
| 加速比 | **1.43×** | | |

**为什么不是 8–12×（诚实说明）**：
1. 热点不是"码⊆单元"的距离计算，而是**候选码生成**（每个单元的 4 子多重集枚举）与每轮全候选去重；这部分仍是 Python 循环（已用 \`SUBCACHE\` 按单元向量缓存，但单元向量很分散）。
2. Windows 下 \`spawn\` 每个 worker 需各自载入 17MB 表（约 0.5 s×12，已并行化）；把表经 \`initargs\` 传递（一次性 pickle 12 次）会**显著更慢**——已改为 worker 自行 load 缓存。
3. 分片按"块数"估计权重（大类优先贪心均衡），但类的工作量还取决于单元数与候选规模，仍有残差。

**下一步可再提速的点**：
- 候选生成向量化：对单元矩阵按 |X| 分桶，用 \`np.unique\`/卷积式统计替代 Python 四重循环；
- 每轮不必重建全候选集：维护"尚未被覆盖单元"的候选计数增量（本实现每轮重算）；
- 把 \`subs_of\` 缓存持久化（pickle）跨进程共享，或预生成 34 张牌的 4-子多重集全集（66,045 个）一次，之后只做包含判定。

## 3. 结果一致性（必须条件）

并行只用于**按类独立**的覆盖计算；**跨类容量协调（排列分配/换码/permfix）全部串行且可重放**：
- \`fastpack.benchmark\` 断言 \`ser[W][0] == par[W][0]\`（每类的码多重集列表逐字段相同）→ **identical: True**；
- 排列分配在 main 中串行执行（见 \`fix_k4.py / fix_k4b.py / chiit_fix.py\`），因此有序码唯一性与容量约束与串行版一致。

## 4. 本轮加速对整体管线的收益

| 环节 | 旧耗时 | 新耗时 |
|---|---|---|
| 每次脚本启动的建表 | 18–27 s | **0.5 s**（缓存） |
| 2846 类逐类覆盖（外推 300 类 → 全部） | 串行 ≈ 15 min | 并行 ≈ 10–11 min（1.43×） |
| 换码/修复（fix_k4b）| 873 s | 未并行（跨类容量协调，必须串行） |

## 5. 文件

| 文件 | 说明 |
|---|---|
| \`fastpack.py\` | table 缓存 + numpy 覆盖 + Pool(12) 基准（\`out/fastpack_bench.json\`） |
| \`out/table_cache.pkl\` | 表缓存（cold 首次生成，之后 load） |
| \`out/fastpack_bench.json\` | 冷/热建表与串行/并行耗时、一致性断言 |
