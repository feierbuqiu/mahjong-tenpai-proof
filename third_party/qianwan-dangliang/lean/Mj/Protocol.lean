/-
  Mj.Protocol —— 协议模型：类键 / 码 / 命中 / 不相交 / 解码表与解码正确性
  只用 core/Std。所有证明为真证明（无 sorry / 无 axiom）。
-/
import Mj.Basic

namespace Mj

/-- 一个码 = 有序 k 元组（长度由表约束） -/
abbrev Code := List Nat

/-- 码的多重集 ⊆ 手牌 -/
def HandContains (H : Hand) (c : Code) : Prop := ∀ t : Fin 34, c.count t.val ≤ H.get t

/-- 类键：该手牌的听牌集合（递增索引列表，唯一标识一个类） -/
def classKey (H : Hand) : List Nat := (waits H).map (fun t => t.val)

/-- 策略表：类键 → 该类可用的码列表 -/
structure Plan where
  codesOf : List Nat → List Code

/-- 表对某手牌 H 在 k 下可用 -/
def Plan.coversHand (P : Plan) (k : Nat) (H : Hand) : Prop :=
  H.total = 13 ∧ ∃ c, c ∈ P.codesOf (classKey H) ∧ c.length = k ∧ HandContains H c

/-- 表在 k 下覆盖全部 13 张听牌手牌 -/
def Plan.coversAll (P : Plan) (k : Nat) : Prop :=
  ∀ H : Hand, H.total = 13 → waits H ≠ [] → P.coversHand k H

/-- 各类码集两两不交 -/
def Plan.disjoint (P : Plan) : Prop :=
  ∀ W1 W2 : List Nat, W1 ≠ W2 → ∀ c : Code, c ∈ P.codesOf W1 → c ∈ P.codesOf W2 → False

/-- 表中所有码长度皆为 k -/
def Plan.lengths (P : Plan) (k : Nat) : Prop :=
  ∀ W : List Nat, ∀ c : Code, c ∈ P.codesOf W → c.length = k

/-- k 可行：存在一张表，长度受限、覆盖全部听牌手牌、各类码集不交 -/
def Feasible (k : Nat) : Prop :=
  ∃ P : Plan, P.lengths k ∧ P.coversAll k ∧ P.disjoint

/-! ## 解码 -/

/-- 按顺序在各类里找第一条含码 c 的类 -/
def decodeIn (P : Plan) : List (List Nat) → Code → Option (List Nat)
  | [], _ => none
  | W :: rest, c => if c ∈ P.codesOf W then some W else decodeIn P rest c

/-- 解码结果必是扫描列表中某个类，且该类确实含码 -/
theorem decodeIn_sound (P : Plan) :
    ∀ {keys : List (List Nat)} {c : Code} {W : List Nat},
      decodeIn P keys c = some W → W ∈ keys ∧ c ∈ P.codesOf W := by
  intro keys
  induction keys with
  | nil => intro c W h; simp [decodeIn] at h
  | cons W0 rest ih =>
    intro c W h
    simp only [decodeIn] at h
    by_cases hc : c ∈ P.codesOf W0
    · simp [hc] at h
      subst h
      exact ⟨List.mem_cons_self, hc⟩
    · simp [hc] at h
      obtain ⟨hmem, hc'⟩ := ih h
      exact ⟨List.mem_cons_of_mem _ hmem, hc'⟩

/-- 若某个类 W 在扫描列表中且含码 c，则解码一定成功 -/
theorem decodeIn_complete (P : Plan) :
    ∀ {keys : List (List Nat)} {c : Code} {W : List Nat},
      W ∈ keys → c ∈ P.codesOf W → ∃ W', decodeIn P keys c = some W' := by
  intro keys
  induction keys with
  | nil => intro c W hmem _; simp at hmem
  | cons W0 rest ih =>
    intro c W hmem hc
    simp only [decodeIn]
    by_cases hc0 : c ∈ P.codesOf W0
    · simp [hc0]
    · simp [hc0]
      rcases List.mem_cons.mp hmem with rfl | hmem'
      · exact absurd hc hc0
      · exact ih hmem' hc

/-- **解码良定义性**：各类码集不交 ⇒ 任何两个含同一码的类相同 -/
theorem decode_unique (P : Plan) (hdisj : P.disjoint)
    {W1 W2 : List Nat} {c : Code}
    (h1 : c ∈ P.codesOf W1) (h2 : c ∈ P.codesOf W2) : W1 = W2 := by
  by_cases h : W1 = W2
  · exact h
  · exact (hdisj W1 W2 h c h1 h2).elim

/-- **解码正确性（协议语义）**：若表覆盖 H（码 c ∈ 类键 W 且 c ⊆ H），
    则 B 从任何包含 W 的扫描表解码得到的类一定与 W 相同（因表不交）。 -/
theorem decode_correct (P : Plan) (hdisj : P.disjoint)
    {keys : List (List Nat)} {W : List Nat} {c : Code}
    (hk : W ∈ keys) (hc : c ∈ P.codesOf W) :
    ∃ W', decodeIn P keys c = some W' ∧ W' = W := by
  obtain ⟨W', hW'⟩ := decodeIn_complete P hk hc
  have hmem := (decodeIn_sound P hW').2
  exact ⟨W', hW', decode_unique P hdisj hmem hc⟩

end Mj
