/-!
# 呆饼问题（二）：听牌信息的排列编码问题 — formal problem statement

This file is the whole trusted statement.  It follows §2 and §7 of
「呆饼问题（二）：听牌信息的排列编码问题.md」 line by line and uses nothing but
Lean core.  Every other file of the development only *proves* things about
these definitions.

Tile numbering (§2.1):
  `0–8` = 1m…9m, `9–17` = 1p…9p, `18–26` = 1s…9s, `27–33` = E S W N P F C.
-/

namespace Tenpai

/-- §2.1  the 34 tile types `T` -/
abbrev Tile := Fin 34

/-- a multiset of tiles, given by its multiplicity function `c_H` -/
abbrev Counts := Tile → Nat

/-- `∑_{t ∈ T} c_H(t)` -/
def total (H : Counts) : Nat := ((List.finRange 34).map H).sum

/-- §2.2  a meld (面子): a sequence of three consecutive number tiles of one suit (顺子),
    or three tiles of one type (刻子) -/
inductive Meld where
  | seq  (t : Tile)   -- the tiles t, t+1, t+2
  | trip (t : Tile)   -- the tiles t, t, t

/-- a sequence must start at rank 1–7 of a number suit, so that it stays inside the suit;
    honours never form sequences -/
def Meld.Valid : Meld → Prop
  | .seq t  => t.val < 27 ∧ t.val % 9 ≤ 6
  | .trip _ => True

/-- multiplicity of tile `s` in a meld -/
def Meld.count : Meld → Tile → Nat
  | .seq t,  s => if s.val = t.val ∨ s.val = t.val + 1 ∨ s.val = t.val + 2 then 1 else 0
  | .trip t, s => if s = t then 3 else 0

/-- §2.2 (1)  standard form: four melds plus one pair (雀头), as a multiset decomposition -/
def IsStandard (G : Counts) : Prop :=
  ∃ (p : Tile) (m₁ m₂ m₃ m₄ : Meld), m₁.Valid ∧ m₂.Valid ∧ m₃.Valid ∧ m₄.Valid ∧
    ∀ s, G s = (if s = p then 2 else 0) + m₁.count s + m₂.count s + m₃.count s + m₄.count s

/-- §2.2 (2)  seven pairs: exactly seven distinct tile types, two copies each
    (four copies of one type never count as two pairs) -/
def IsSevenPairs (G : Counts) : Prop :=
  ∃ S : List Tile, S.Nodup ∧ S.length = 7 ∧ ∀ s, G s = if s ∈ S then 2 else 0

/-- the 13 terminal and honour types (幺九牌与字牌): 1 and 9 of each suit, and the 7 honours -/
def IsOrphan (t : Tile) : Prop :=
  (t.val < 27 ∧ (t.val % 9 = 0 ∨ t.val % 9 = 8)) ∨ 27 ≤ t.val

instance : DecidablePred IsOrphan := fun t => by unfold IsOrphan; infer_instance

/-- §2.2 (3)  thirteen orphans: one of each of the 13 types plus a second copy of one of them -/
def IsKokushi (G : Counts) : Prop :=
  ∃ o, IsOrphan o ∧ ∀ s, G s = (if IsOrphan s then 1 else 0) + (if s = o then 1 else 0)

/-- §2.2  the set `𝒢` of legal 14-tile winning multisets (no type more than 4 times) -/
def IsWinning (G : Counts) : Prop :=
  (∀ s, G s ≤ 4) ∧ (IsStandard G ∨ IsSevenPairs G ∨ IsKokushi G)

/-- `H ⊎ {t}` -/
def addTile (H : Counts) (t : Tile) : Counts := fun s => if s = t then H s + 1 else H s

/-- §2.3  the wait set `W(H) = { t ∈ T : c_H(t) < 4 ∧ H ⊎ {t} ∈ 𝒢 }` -/
def W (H : Counts) : Tile → Prop := fun t => H t < 4 ∧ IsWinning (addTile H t)

/-- a legal 13-tile hand (§2.1) -/
def IsHand (H : Counts) : Prop := total H = 13 ∧ ∀ t, H t ≤ 4

/-- §2.3  the set `ℋ` of all admissible inputs: legal 13-tile hands with `W(H) ≠ ∅` -/
def InH (H : Counts) : Prop := IsHand H ∧ ∃ t, W H t

/-- §7  `A_k(H)`: ordered k-tuples that use no tile more often than `H` contains it -/
def Admissible (H : Counts) {k : Nat} (v : Fin k → Tile) : Prop :=
  ∀ t, (List.finRange k).countP (fun j => v j = t) ≤ H t

/-- §7  `k` is feasible: there is `f : ℋ → T^k` with `f(H) ∈ A_k(H)` such that
    `f(H) = f(H') ⇒ W(H) = W(H')` -/
def Feasible (k : Nat) : Prop :=
  ∃ f : {H // InH H} → (Fin k → Tile),
    (∀ H, Admissible H.1 (f H)) ∧ ∀ H H', f H = f H' → W H.1 = W H'.1

/-- §7  `n = k* = min { k ∈ {0,…,13} : k feasible }` -/
def IsKStar (n : Nat) : Prop :=
  n ≤ 13 ∧ Feasible n ∧ ∀ k, k ≤ 13 → Feasible k → n ≤ k

end Tenpai
