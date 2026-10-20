# L8 交接：l6Total 与原定义桥接（task-18，analyst-lower）

## 0. 最终状态（方案 b：条件形式，Lead 已授权）
- 交付文件：lean/Mj/L6Bridge.lean（174 行，编译通过：lake env lean Mj/L6Bridge.lean 退出码 0，1.6 s，峰值 454 MB，无 error / 无 sorry / 无自造 axiom）。
- 主结论（条件形式）：
      theorem l6Total_eq (h : l6BatchStats = idx16.map batchAt) :
          l6Total = (309144, 0, 5402697, 0)
  由 l6Total_eq_totalIdx h : l6Total = totalIdx（本文件，纯重写）+ Mj.L6Total.totalIdx_eq（Lead，16 批内核拼合）得到。
- 唯一未内核化输入 h：l6BatchStats = idx16.map batchAt，即「16 批、每批 20,000 块」的数据层事实
  （309,144 = 15x20,000 + 9,144；verifier task-19 已独立确认分批与 recs[i:i+20000] 一致）。
  它的自然证明 l6BatchStats_eq_idx16 (h : l6Batches.length = 16) 会踩第 2 节的展开陷阱，故降级为假设并如实标注。

## 1. 实测 axioms（文件末尾已固化）
    Mj.map_range_getD_eq_self  [propext, Quot.sound]
    Mj.upper2_lam_eq_add4      [Quot.sound]
    Mj.foldl_eq_of_fun_eq      []                        -- 无公理
    Mj.go_len                  [propext, Quot.sound]
    Mj.chunkBlocks_length      [propext, Quot.sound]
    Mj.l6Batches_length_of     [propext, Quot.sound]     -- 条件：blocks.length = 309144
    Mj.l6Batches_eq_idx16      [propext, Quot.sound]     -- 条件：l6Batches.length = 16
    Mj.l6Total_eq_totalIdx     [propext, Quot.sound]     -- 条件：h
    Mj.l6Total_eq              [propext, Quot.sound] + l6_batch00..15_eq 的 16 条 native_decide 可信基
  => 无 iiUnitsComplete、无 sorry、无自定义 axiom；条件之外的推理全部内核级。

## 2. 关键工程教训（25 GB OOM 与多次 maxRecDepth 换来的）
在 Lean 里，任何对 l6Batches / batchAt / l6BatchStats / chunkBlocks 的 rw / simp / rcases / rfl-defeq 匹配，
都可能 delta-展开成 l6Batches -> chunkBlocks 20000 blocks -> blocks.length（309k 字面表整体求值），
=> 3–25 GB 或 maximum recursion depth。

具体触发过的写法（不要用）：
- rcases batchAt q with（q 是符号变量） => 24–25 GB（Lead 定位到行号）；
- simp only [Function.comp_apply, batchAt] => 25 GB；
- congr 1 比较含 batchAt i 的 lambda => maxRecDepth；
- rw [l6Batches] / rw [hb]（改写 fuel 表达式） => maxRecDepth。

安全写法（本文件采用）：
- 只在「定义展开后两侧同构」之处用 rfl；
- 用 congrArg 改写 l6BatchStats 这类不透明项；
- 用函数级等式 upper2_lam_eq_add4 把 Upper2 的累加 lambda 与 add4 对齐（只在变量上 funext/rcases），
  再用 foldl_eq_of_fun_eq（f/g 是不透明函数参数）；
- List.foldl_map 只作为终结项应用，不做重写匹配。

另一条教训：blkChunk* / blkB* / blocks 这类大表，kernel rfl / decide 与 native_decide 都不可行（见第 3 节）。

## 3. 实测数据（单进程；均为该 lean 进程自身 WorkingSet64 峰值）
| 目标 | 方法 | 结果 |
|---|---|---|
| l6Batches.length = 16 | native_decide | 19 GB / 197 s 未完成（Lead 实测，被杀） |
| blocks.length = 309144 | kernel rfl（maxRecDepth 2e6，空闲机器） | 16 GB / 900 s 仍未完成（预算上限，守卫杀） |
| blocks.length = 309144 | kernel decide（maxRecDepth 2e6，空闲） | 257 s 时 6.15 GB（6 GB 守卫杀） |
| blocks.length = 309144 | kernel decide（默认 depth） | 8.3 s 报 maximum recursion depth |
| ([blkB0..blkB161].map List.length).sum | decide（maxRecDepth 8000） | 323 s 时 3.08 GB（杀） |
| blkB0.length = 1920 | decide（maxRecDepth 1e5） | 通过，约 10 s/条（162 条约 27 min，太慢） |
| blkChunkK.length = 30 | decide（默认） | 通过，约 20 ms/条（10,305 条约 3.4 min / 532 MB） |
| 162 条 blkB*_len（length_append 逐层拼） | simp only [blkB*, List.length_append, lc…] | 失败：blkB 层 deterministic timeout at whnf |
| lenT blocks 0 = 309144（自写尾递归计数器） | decide（maxRecDepth 2e6） | 超过 13 min 未完成（手动停） |

=> 结论：L8 的数值部分在 Lean 里没有便宜路径；h 因此如实标注为唯一未内核化输入。

## 4. 结论链（本文件内）
1. map_range_getD_eq_self：(List.range l.length).map (l.getD · d) = l（Std 无，自证）。
2. idx16_eq_range：字面表 idx16 = List.range 16。
3. upper2_lam_eq_add4：Upper2 的累加 lambda = add4（函数级）。
4. foldl_eq_of_fun_eq：函数相等 => foldl 相等（无公理）。
5. go_eq_zero / go_eq_succ / go_len / chunkBlocks_length：Lean 把 chunkBlocks 的 let rec go 提升为 chunkBlocks.go；
   go_len : (chunkBlocks.go 20000 f ys).length = min f 向上取整(|ys|/20000)（对 fuel 归纳 + omega，除数 20000 为字面量）。
6. l6Batches_length_of (hb : blocks.length = 309144) : l6Batches.length = 16（条件）。
7. l6Batches_eq_idx16 (h : l6Batches.length = 16)（条件）。
8. l6Total_eq_totalIdx (h : l6BatchStats = idx16.map batchAt) : l6Total = totalIdx。
9. l6Total_eq (h) : l6Total = (309144, 0, 5402697, 0) = 前一条与 totalIdx_eq 的传递。

## 5. 后续若要彻底消掉 h（给接手的人）
需要的两条之一（卡在同一处）：(i) blocks.length = 309144（内核）；或 (ii) 直接 l6BatchStats = idx16.map batchAt。
已排除的路线见第 3 节（native / kernel decide / rfl / 分块求和 / 逐块拼接）。
唯一还有希望的路线：把 162 条 blkB*_len 拆成独立小模块（Lake 并行，每个模块只做一条 length_append 链），
最后再拼 blocks_length；这样每次 whnf 规模小、不进同一个心跳预算。预估 30–60 min + 一次全库构建；性价比低。

## 6. 遗留脆弱点
1. chunkBlocks.go 是 let rec 的提升名：Lean 升级若改名会在编译期报错（不静默）；用 #print chunkBlocks 看新名。
2. go_len 依赖批大小为字面量 20000（omega 才能处理除法）；改成变量需换 Nat.div 引理。
3. 长度事实依赖 Data2 的结构（162 个 blkB*、10,305 个 blkChunk*、仅最后一块 24 项）；数据重生成后要重跑核对。
4. 本文件未被 lean/Mj.lean import => 不在 lake 默认目标里（Lake module glob 配置期缓存，见 work/lowerbound/HANDOFF.md 第 9.7 节）；
   要进默认构建请加 import Mj.L6Bridge（Lead 操作）。
5. lean/Mj/L6Len.lean 是本次失败实验的留档（已改成纯注释文件，不含定理，不会破坏构建）。
