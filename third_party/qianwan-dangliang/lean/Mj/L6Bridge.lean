/-
  Mj.L6Bridge —— L8 桥接引理（task-18, analyst-lower）

  【降级处理：Lead 方案 (b)】唯一未内核化输入以**假设**形式给出：
      h : l6BatchStats = idx16.map batchAt
    （= 「16 批、每批 20,000 块」这一数据层事实；verifier task-19 已独立确认）

  主结论（条件形式）：
      theorem l6Total_eq (h : l6BatchStats = idx16.map batchAt) :
          l6Total = (309144, 0, 5402697, 0)
  = l6Total_eq_totalIdx h（l6Total = totalIdx）+ totalIdx_eq（Lead，16 批内核拼合）。

  ⚠️ 关键实现约束（25 GB OOM + 多次 maxRecDepth 换来的教训）：
  在 Lean 里任何对 l6Batches / batchAt / l6BatchStats / chunkBlocks 的 rw/simp/rcases/
  rfl-defeq 尝试，都可能 delta-展开 l6Batches → chunkBlocks 20000 blocks →
  求值 blocks.length（309k 字面表）⇒ 3–25 GB 或 maxRecDepth。
  因此本文件的桥接链只用：
    · rfl 只在「定义展开后两侧同构」之处（l6Total、totalIdx、upper2_lam_eq_add4）；
    · congrArg + 函数级等式把 add4 与 Upper2 的累加 lambda 对齐（batchAt 只作不透明函数参数）；
    · List.foldl_map 只作为终结项应用（不做任何重写匹配）。
  由此完全避开「batchAt 在符号变量上被求值」。

  为什么 h 没能内核化（实测，详见 work/lean/L8_HANDOFF.md）：
    * native_decide 直接算 l6Batches.length / blocks.length：19 GB / 197 s 未完成；
    * 内核 rfl 算 blocks.length = 309144：16 GB / 900 s 仍未完成（Lead 给的预算上限）；
    * 内核 decide：257 s 时 6.15 GB（自设守卫杀）；
    * 分块求和 decide：323 s / 3.08 GB（杀）；
    * 逐块核对路线（10,305 条 blkChunkK.length 内核 decide ≈3.4 min/532 MB 可过）
      + 162 条 blkB*_len（length_append 逐层拼接）⇒ blkB 层触发
      (deterministic) timeout at whnf 而失败；其 blkB0.length 单条 decide≈10 s（162 条≈27 min）。
  ⇒ L8 的数值部分在 Lean 里没有便宜路径；h 如实标注为唯一未内核化输入。

  信任基：#print axioms l6Total_eq = 常规内核公理 + totalIdx_eq 的 16 条 native_decide
  可信基；无 iiUnitsComplete、无 sorry、无自造 axiom。
-/
import Mj.L6Total

set_option maxHeartbeats 0

namespace Mj

/-! ## 1. 通用引理（core/Std 无现成者，全部内核级） -/

/-- (List.range l.length).map (l.getD · d) = l；用 Std 的
    List.range_succ_eq_map / map_cons / map_map / getD_cons_zero / getD_cons_succ。 -/
theorem map_range_getD_eq_self {α : Type} (d : α) (l : List α) :
    (List.range l.length).map (fun i => l.getD i d) = l := by
  induction l with
  | nil => rfl
  | cons a t ih =>
    rw [List.length_cons, List.range_succ_eq_map, List.map_cons, List.map_map, List.getD_cons_zero]
    have hcomp : ((fun i => (a :: t).getD i d) ∘ Nat.succ) = (fun i => t.getD i d) := by
      funext i
      exact List.getD_cons_succ
    rw [hcomp, ih]

/-- 字面索引表 idx16 = List.range 16 -/
theorem idx16_eq_range : idx16 = List.range 16 := by decide

/-- Upper2 的累加 lambda = L6Index.add4（只在变量上 funext/rcases） -/
theorem upper2_lam_eq_add4 :
    (fun (a, b, c, d) (x, y, z, w) => (a + x, b + y, c + z, d + w))
      = (add4 : Nat × Nat × Nat × Nat → Nat × Nat × Nat × Nat → Nat × Nat × Nat × Nat) := by
  funext p x
  rcases p with ⟨a, b, c, d⟩
  rcases x with ⟨x, y, z, w⟩
  rfl

/-- foldl 在函数级等式下不变（f g 都是不透明函数参数，不做任何展开） -/
theorem foldl_eq_of_fun_eq {α β : Type} {f g : α → β → α} (h : f = g)
    (l : List β) (init : α) : l.foldl f init = l.foldl g init := by
  rw [h]

/-! ## 2. chunkBlocks 的批数（结构归纳；不触碰 309k 字面表） -/

/-- Lean 把 chunkBlocks 里的 let rec go 提升为 chunkBlocks.go；fuel = 0 时为空 -/
theorem go_eq_zero (ys : List Nat) : chunkBlocks.go 20000 0 ys = [] := rfl

/-- fuel = f+1 时的展开 -/
theorem go_eq_succ (f : Nat) (ys : List Nat) :
    chunkBlocks.go 20000 (f + 1) ys
      = (if ys.isEmpty then []
         else ys.take 20000 :: chunkBlocks.go 20000 f (ys.drop 20000)) := rfl

/-- go f ys 产出的批数 = min(燃料, ⌈|ys|/20000⌉) -/
theorem go_len (f : Nat) (ys : List Nat) :
    (chunkBlocks.go 20000 f ys).length = min f ((ys.length + 19999) / 20000) := by
  induction f generalizing ys with
  | zero => rw [go_eq_zero]; simp
  | succ f ih =>
    rw [go_eq_succ]
    by_cases h : ys.isEmpty
    · rw [if_pos h, List.isEmpty_iff_length_eq_zero.mp h]
      simp
    · rw [if_neg h, List.length_cons, ih, List.length_drop]
      have hne : ys ≠ [] := by rw [List.isEmpty_iff] at h; exact h
      have hpos : 0 < ys.length := by
        rw [List.length_pos_iff]
        exact hne
      omega

/-- 批数公式：(chunkBlocks 20000 xs).length = ⌈|xs|/20000⌉ -/
theorem chunkBlocks_length (xs : List Nat) :
    (chunkBlocks 20000 xs).length = (xs.length + 19999) / 20000 := by
  rw [chunkBlocks, go_len]
  omega

/-- 条件形式：给定 blocks.length = 309144（内核里未拿下，见文件头），批数 = 16。 -/
theorem l6Batches_length_of (hb : blocks.length = 309144) : l6Batches.length = 16 := by
  have h1 : l6Batches = chunkBlocks 20000 blocks := rfl
  have h2 : (chunkBlocks 20000 blocks).length = (blocks.length + 19999) / 20000 :=
    chunkBlocks_length blocks
  have h3 : (blocks.length + 19999) / 20000 = (309144 + 19999) / 20000 :=
    congrArg (fun n => (n + 19999) / 20000) hb
  have h4 : (309144 + 19999) / 20000 = 16 := by decide
  exact (congrArg List.length h1).trans (h2.trans (h3.trans h4))

/-! ## 3. 桥接（只 rfl / congrArg / foldl_map；batchAt 仅作不透明函数参数） -/

/-- l6Batches 就是「按下标 getD」的表（需要批数 = 16 或等价的长度事实）。 -/
theorem l6Batches_eq_idx16 (h : l6Batches.length = 16) :
    l6Batches = idx16.map (fun i => l6Batches.getD i []) := by
  have hmap : l6Batches = (List.range l6Batches.length).map (fun i => l6Batches.getD i []) :=
    (map_range_getD_eq_self [] l6Batches).symm
  have hlen : (List.range l6Batches.length).map (fun i => l6Batches.getD i [])
      = (List.range 16).map (fun i => l6Batches.getD i []) :=
    congrArg (fun n => (List.range n).map (fun i => l6Batches.getD i [])) h
  have hidx : (List.range 16).map (fun i => l6Batches.getD i [])
      = idx16.map (fun i => l6Batches.getD i []) :=
    congrArg (fun l => l.map (fun i => l6Batches.getD i [])) idx16_eq_range.symm
  exact hmap.trans (hlen.trans hidx)

/-! ## 4. 汇总 = totalIdx -/

/-- **仅在此处需要未内核化输入 h**：批统计表 = 16 批的 batchAt 表。
    （h 的自然证明 l6BatchStats_eq_idx16 会触发 batchAt/getD/l6Batches 展开陷阱，
      见文件头；这里把它作为假设。） -/
theorem l6Total_eq_totalIdx (h : l6BatchStats = idx16.map batchAt) : l6Total = totalIdx := by
  have h1 : l6Total = l6BatchStats.foldl
        (fun (a, b, c, d) (x, y, z, w) => (a + x, b + y, c + z, d + w)) (0, 0, 0, 0) := rfl
  have h2 : l6BatchStats.foldl
        (fun (a, b, c, d) (x, y, z, w) => (a + x, b + y, c + z, d + w)) (0, 0, 0, 0)
      = (idx16.map batchAt).foldl
        (fun (a, b, c, d) (x, y, z, w) => (a + x, b + y, c + z, d + w)) (0, 0, 0, 0) :=
    congrArg (fun l => l.foldl
      (fun (a, b, c, d) (x, y, z, w) => (a + x, b + y, c + z, d + w)) (0, 0, 0, 0)) h
  have h3 : (idx16.map batchAt).foldl
        (fun (a, b, c, d) (x, y, z, w) => (a + x, b + y, c + z, d + w)) (0, 0, 0, 0)
      = (idx16.map batchAt).foldl add4 (0, 0, 0, 0) :=
    foldl_eq_of_fun_eq upper2_lam_eq_add4 (idx16.map batchAt) (0, 0, 0, 0)
  have h4 : (idx16.map batchAt).foldl add4 (0, 0, 0, 0)
      = idx16.foldl (fun acc i => add4 acc (batchAt i)) (0, 0, 0, 0) := List.foldl_map
  have h5 : idx16.foldl (fun acc i => add4 acc (batchAt i)) (0, 0, 0, 0) = totalIdx := rfl
  exact h1.trans (h2.trans (h3.trans (h4.trans h5)))

/-! ## 5. 主定理（条件形式） -/

/-- l6Total = (309144, 0, 5402697, 0)，唯一未内核化输入 h：
    l6BatchStats = idx16.map batchAt（= 16 批 × 20,000 块的数据层事实）。 -/
theorem l6Total_eq (h : l6BatchStats = idx16.map batchAt) :
    l6Total = (309144, 0, 5402697, 0) :=
  (l6Total_eq_totalIdx h).trans totalIdx_eq

#print axioms map_range_getD_eq_self
#print axioms upper2_lam_eq_add4
#print axioms foldl_eq_of_fun_eq
#print axioms go_len
#print axioms chunkBlocks_length
#print axioms l6Batches_length_of
#print axioms l6Batches_eq_idx16
#print axioms l6Total_eq_totalIdx
#print axioms l6Total_eq

end Mj