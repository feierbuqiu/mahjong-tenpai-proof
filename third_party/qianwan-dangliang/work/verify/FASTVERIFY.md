# FASTVERIFY.md — 复核工具并行化（2026-09-17）

> 目标：全套复核 < 1 分钟；实测 **34.7 秒**（12 进程）。机器：Intel i5-10600K（6 物理核 / 12 逻辑核）。

## 1. 新旧耗时对照（同一 plan：work/verify/plan_k4_final.json，411,508 条码，2,846 类）

| 项目 | 旧（串行） | 新（12 进程） | 加速比 | 备注 |
|---|---|---|---|---|
| Type I 块级覆盖（166,746 块） | 394 s（resid_check.py 单进程 DFS） | **18.9 s** | **20.8x** | 先 numpy 预筛『是否存在码 ⊆ A』，未命中才 DFS |
| chiitoi 精确描述子（97 个） | ~60 s（chk_chiitoi.py 单进程） | **7.1 s** | **8.5x** | 改为 bitmask 分支搜索（含/不含最低位顶点）|
| 10^6 手结构化模拟 | ~120 s（30 万手约 36 s，外推） | **7.5 s** | **16x** | 按手数切块并行 + 类码矩阵向量化判定 |
| 单花色全量覆盖（4 门 288,675 手） | 0.6 s（fastcov.py，已向量化） | **0.8 s** | ~1x | 已是最优，无并行价值（保持为回归基准） |
| 全套合计 | ~700–770 s（verify_strategy.py 13 分钟） | **34.7 s** | **约 20x** | 见 fastverify_report.json |

CPU 利用率：12 个 worker 全程满载（`Pool(12, initializer=_init)` + 细粒度切块 `jobs = nproc*16 = 192`），
主进程只做汇总；W 计算**不在热路径**（全部走 cache_w_*.npz）。

## 2. 语义等价（回归测试）

同一 plan 上新旧结果逐字段一致：

| 字段 | 旧工具 | fastverify_k4.py | 一致 |
|---|---|---|---|
| 类集 = 2846 / 0 空类 / 有序码唯一 | structural_k4.py ✓ | struct 段 ✓ | ✓ |
| Type I 未覆盖 | 47（resid_check.py） | **47** | ✓ |
| chiitoi 失败描述子 | 77（chk_chiitoi.py 精确） | **77** | ✓ |
| 单花色未覆盖手牌 | 0/0/0/0（fastcov.py） | **0** | ✓ |
| 模拟失败率 | 8,301/300,000 = 2.77% | 27,984/1,000,000 = 2.80% | 同量级（样本数不同） |

注：fastverify 的 chiitoi 快路径**只返回失败计数**（witness_K 为 null）；需要见证手牌时仍用 chk_chiitoi.py。

## 3. 用法

    python -u work/verify/fastverify_k4.py work/verify/plan_k4_final.json 1000000

输出 work/verify/fastverify_report.json，含 struct / typeI / chiitoi / sim / single_suit_uncovered / timing 六段。

## 4. 实现要点（照搬给其它工具）

1. **只读数据在 initializer 载入一次**：plan（类 → (n×34) int8 计数矩阵）、global.json 的 Type I sources、W 缓存 npz、chiitoi 描述子。
2. **numpy 快路径优先**：『是否存在码 ⊆ A』= `(M <= A).all(axis=1).any()`；命中即判覆盖（语义与 DFS 根节点捷径完全一致），未命中再 DFS（慢路径）。
3. **细粒度切块**（nproc×16）平衡负载；chiitoi 与模拟按描述子数/手数切分。
4. 热路径不做 W 计算（用缓存）；缓存口径变化时必须 `fastcov.py <plan> --rebuild`。

## 5. 已知边界

- (a) 仍只覆盖 **kind I** 来源；kind II 依赖模拟与 DFS 抽样（见 HANDOFF §6.4）。
- 模拟失败是**抽样**指标；精确覆盖要用全量单花色 + 描述子判定。