import Tenpai.Cover0
import Tenpai.CheckSound2

/-!
# Lower bound: no `k ≤ 3` is feasible

347 hands whose tiles all lie in `U = {2m, …, 8m}` have pairwise different wait sets
(kernel check `witOK`).  A code of such a hand uses only tiles of `U`, so it is one of at most
`7^k ≤ 343 < 347` tuples; two of the hands would share a code.
-/

namespace Tenpai

/-- the hand of a witness (a packed vector of the `m` suit) -/
def witHand (u : Nat) : Counts := fun s => if s.val < 9 then fld u s.val else 0

theorem strictInc_big : ∀ (l : List Nat) (c : Nat), strictInc (c :: l) = true → ∀ x ∈ l, c < x
  | [], _, _ => by simp
  | d :: l, c, hc => by
    intro x hx
    have hc' : (Nat.blt c d && strictInc (d :: l)) = true := hc
    rw [Bool.and_eq_true] at hc'
    have hcd : c < d := Nat.blt_eq.mp hc'.1
    rcases List.mem_cons.mp hx with rfl | hx
    · exact hcd
    · exact Nat.lt_trans hcd (strictInc_big l d hc'.2 x hx)

theorem strictInc_nodup : ∀ (l : List Nat), strictInc l = true → l.Nodup
  | [], _ => List.nodup_nil
  | [a], _ => by simp
  | a :: b :: l, h => by
    have h' : (Nat.blt a b && strictInc (b :: l)) = true := h
    rw [Bool.and_eq_true] at h'
    rw [List.nodup_cons]
    refine ⟨?_, strictInc_nodup (b :: l) h'.2⟩
    intro hmem
    have := strictInc_big (b :: l) a h a hmem
    omega

/-- the witnesses: valid hands inside `U`, tenpai, with pairwise different wait masks -/
theorem wit_sound (ws : List Nat) (h : witOK ws = true) :
    (∀ u ∈ ws, witValid u = true) ∧ (∀ u ∈ ws, wAll (mOnly u) ≠ 0) ∧ (ws.map (fun u => wAll (mOnly u))).Nodup := by
  unfold witOK at h
  simp only [Bool.and_eq_true] at h
  obtain ⟨⟨h1, h2⟩, h3⟩ := h
  refine ⟨(allL_iff _ _).mp h1, fun u hu => ?_, strictInc_nodup _ h3⟩
  have := (allL_iff _ _).mp h2 u hu
  simp only [Bool.not_eq_true'] at this
  intro e; rw [e] at this; simp at this

theorem inj_of_nodup_map {α β : Type} (f : α → β) : ∀ (l : List α), (l.map f).Nodup →
    ∀ a ∈ l, ∀ b ∈ l, f a = f b → a = b
  | [], _, a, ha, _, _, _ => by simp at ha
  | c :: l, h, a, ha, b, hb, he => by
    rw [List.map_cons, List.nodup_cons] at h
    rcases List.mem_cons.mp ha with h1 | ha' <;> rcases List.mem_cons.mp hb with h2 | hb'
    · rw [h1, h2]
    · rw [h1] at he; exact absurd (List.mem_map.mpr ⟨b, hb', he.symm⟩) h.1
    · rw [h2] at he; exact absurd (List.mem_map.mpr ⟨a, ha', he⟩) h.1
    · exact inj_of_nodup_map f l h.2 a ha' b hb' he

/-! ## the witness hands -/

section witness
variable (u : Nat) (hu : witValid u = true)
include hu

theorem witValid_iff : u < 2 ^ 36 ∧ fld u 0 = 0 ∧ fld u 8 = 0 ∧ (∀ j < 9, fld u j ≤ 4) ∧ sumFields u 9 = 13 := by
  unfold witValid at hu
  simp only [Bool.and_eq_true, Nat.blt_eq, Nat.beq_eq] at hu
  obtain ⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩ := hu
  refine ⟨?_, h2, h3, fun j hj => ?_, h5⟩
  · have : Nat.shiftLeft 1 36 = 2 ^ 36 := by rw [shift_one]
    rw [this] at h1; exact h1
  · have := (allBelow_iff _ 9).mp h4 j hj; simpa [Nat.ble_eq] using this

theorem witHand_le : ∀ s, witHand u s ≤ 4 := by
  intro s; unfold witHand; split
  · exact (witValid_iff u hu).2.2.2.1 _ (by omega)
  · omega

end witness

theorem sumFields_eq (v : Nat) : ∀ n, sumFields v n = sumF (fld v) n
  | 0 => rfl
  | n + 1 => by
    show Nat.add (sumFields v n) (fld v n) = _
    rw [sumFields_eq v n]; rfl

section witness2
variable (u : Nat) (hu : witValid u = true)
include hu

theorem witHand_hand : IsHand (witHand u) := by
  refine ⟨?_, witHand_le u hu⟩
  rw [total_eq_sizes]
  have hs := (witValid_iff u hu).2.2.2.2
  rw [sumFields_eq] at hs
  have h0 : hsize (witHand u) 0 = sumF (fld u) 9 := by
    unfold hsize; apply sumF_congr; intro j hj
    have hj' : j < 9 := by unfold catLen at hj; simpa using hj
    simp [catF, extF, witHand, show j < 34 by omega, hj']
  have hz : ∀ k, 1 ≤ k → k < 4 → hsize (witHand u) k = 0 := by
    intro k hk1 hk4
    unfold hsize
    rw [sumF_congr (g := fun _ => 0) (fun j hj => by
      have := catLen_le k hk4 j hj
      simp only [catF, extF, this, dite_true, witHand]
      rw [ite_eq_right (by unfold catLen at hj; split at hj <;> omega)])]
    generalize catLen k = n
    induction n with
    | zero => rfl
    | succ n ih => rw [sumF_succ, ih]
  rw [h0, hz 1 (by omega) (by omega), hz 2 (by omega) (by omega), hz 3 (by omega) (by omega), hs]

theorem cvOf_witHand : ∀ k < 4, cvOf (witHand u) k = mOnly u k := by
  have hv := witValid_iff u hu
  intro k hk
  rcases (show k = 0 ∨ 1 ≤ k by omega) with rfl | hk1
  · show pkF (catF (extF (witHand u)) 0) (catLen 0) = u
    have : pkF (catF (extF (witHand u)) 0) (catLen 0) = pkF (fld u) 9 :=
      pkF_congr (fun j hj => by
        have hj' : j < 9 := by unfold catLen at hj; simpa using hj
        simp [catF, extF, witHand, show j < 34 by omega, hj'])
    rw [this, pkF_fld u 9 (by have := hv.1; omega)]
  · show pkF (catF (extF (witHand u)) k) (catLen k) = cond (Nat.beq k 0) u 0
    have hb : Nat.beq k 0 = false := by
      cases h : Nat.beq k 0
      · rfl
      · exact absurd (Nat.eq_of_beq_eq_true h) (by omega)
    rw [hb, Bool.cond_false]
    rw [pkF_congr (g := fun _ => 0) (fun j hj => by
      have := catLen_le k hk j hj
      simp only [catF, extF, this, dite_true, witHand]
      rw [ite_eq_right (by unfold catLen at hj; split at hj <;> omega)])]
    exact pkF_zero_fn _

theorem wit_mask : wAll (cvOf (witHand u)) = wAll (mOnly u) := wAll_congr _ _ (cvOf_witHand u hu)

/-- the tiles of a witness are in `2m … 8m` -/
theorem witHand_support (s : Tile) (h : witHand u s ≠ 0) : 1 ≤ s.val ∧ s.val ≤ 7 := by
  have hv := witValid_iff u hu
  unfold witHand at h
  split at h
  · next hs =>
    constructor
    · exact Decidable.byContradiction fun hn => h (by rw [show s.val = 0 by omega]; exact hv.2.1)
    · exact Decidable.byContradiction fun hn => h (by rw [show s.val = 8 by omega]; exact hv.2.2.1)
  · exact absurd rfl h

end witness2

/-! ## the pigeonhole argument -/

/-- two hands with the same wait set have the same mask -/
theorem mask_of_W (H H' : Counts) (hH : IsHand H) (hH' : IsHand H') (h : W H = W H') :
    wAll (cvOf H) = wAll (cvOf H') := by
  apply mask_eq_of (wAll_high H hH) (wAll_high H' hH')
  intro i hi
  rw [wAll_correct H hH ⟨i, hi⟩, wAll_correct H' hH' ⟨i, hi⟩, h]

/-- an ordered code over `2m … 8m` as a number `< 7^k` -/
def enc7 : (k : Nat) → (Fin k → Tile) → Nat
  | 0, _ => 0
  | k + 1, c => ((c 0).val - 1) + 7 * enc7 k (fun j => c j.succ)

theorem enc7_lt : ∀ (k : Nat) (c : Fin k → Tile), (∀ j, 1 ≤ (c j).val ∧ (c j).val ≤ 7) → enc7 k c < 7 ^ k
  | 0, _, _ => by simp [enc7]
  | k + 1, c, h => by
    have := enc7_lt k (fun j => c j.succ) (fun j => h j.succ)
    have h0 := h 0
    show ((c 0).val - 1) + 7 * enc7 k (fun j => c j.succ) < 7 ^ (k + 1)
    rw [Nat.pow_succ]
    omega

theorem enc7_inj : ∀ (k : Nat) (c c' : Fin k → Tile), (∀ j, 1 ≤ (c j).val ∧ (c j).val ≤ 7) →
    (∀ j, 1 ≤ (c' j).val ∧ (c' j).val ≤ 7) → enc7 k c = enc7 k c' → c = c'
  | 0, c, c', _, _, _ => funext (fun j => j.elim0)
  | k + 1, c, c', h, h', he => by
    have he' : ((c 0).val - 1) + 7 * enc7 k (fun j => c j.succ) = ((c' 0).val - 1) + 7 * enc7 k (fun j => c' j.succ) := he
    have h0 := h 0
    have h0' := h' 0
    have hlt := enc7_lt k (fun j => c j.succ) (fun j => h j.succ)
    have hlt' := enc7_lt k (fun j => c' j.succ) (fun j => h' j.succ)
    have hz : c 0 = c' 0 := Fin.ext (by omega)
    have ht := enc7_inj k (fun j => c j.succ) (fun j => c' j.succ) (fun j => h j.succ) (fun j => h' j.succ) (by omega)
    funext j
    refine Fin.cases ?_ (fun j => ?_) j
    · exact hz
    · exact congrFun ht j

/-- **the lower bound**: given the checked witnesses, no `k ≤ 3` is feasible -/
theorem not_feasible_le3 (ws : List Nat) (hws : witOK ws = true) (hlen : ws.length = 347)
    (k : Nat) (hk : k ≤ 3) : ¬ Feasible k := by
  rintro ⟨f, hadm, hdec⟩
  obtain ⟨hval, hnz, hnd⟩ := wit_sound ws hws
  have hin : ∀ u ∈ ws, InH (witHand u) := by
    intro u hu
    refine ⟨witHand_hand u (hval u hu), ?_⟩
    have hm := hnz u hu
    rw [← wit_mask u (hval u hu)] at hm
    obtain ⟨i, hi⟩ := testBit_of_ne_zero hm
    have hi34 : i < 34 := Decidable.byContradiction fun hn => by
      rw [wAll_high _ (witHand_hand u (hval u hu)) i (by omega)] at hi; exact Bool.noConfusion hi
    exact ⟨⟨i, hi34⟩, (wAll_correct _ (witHand_hand u (hval u hu)) ⟨i, hi34⟩).mp hi⟩
  -- the code of a witness
  let code : Nat → (Fin k → Tile) := fun u =>
    if h : u ∈ ws then f ⟨witHand u, hin u h⟩ else fun _ => ⟨1, by omega⟩
  have hcode_range : ∀ u ∈ ws, ∀ j, 1 ≤ (code u j).val ∧ (code u j).val ≤ 7 := by
    intro u hu j
    simp only [code, hu, dite_true]
    have hc := hadm ⟨witHand u, hin u hu⟩ (f ⟨witHand u, hin u hu⟩ j)
    have hpos : 0 < (List.finRange k).countP (fun i => f ⟨witHand u, hin u hu⟩ i = f ⟨witHand u, hin u hu⟩ j) :=
      List.countP_pos_iff.mpr ⟨j, List.mem_finRange j, by simp⟩
    have hc' : (List.finRange k).countP (fun i => f ⟨witHand u, hin u hu⟩ i = f ⟨witHand u, hin u hu⟩ j)
        ≤ witHand u (f ⟨witHand u, hin u hu⟩ j) := hc
    exact witHand_support u (hval u hu) _ (by omega)
  -- distinct witnesses get distinct codes
  have hinj : ∀ a ∈ ws, ∀ b ∈ ws, enc7 k (code a) = enc7 k (code b) → a = b := by
    intro a ha b hb he
    have hc := enc7_inj k _ _ (hcode_range a ha) (hcode_range b hb) he
    simp only [code, ha, hb, dite_true] at hc
    have hW := hdec ⟨witHand a, hin a ha⟩ ⟨witHand b, hin b hb⟩ hc
    have hm := mask_of_W _ _ (witHand_hand a (hval a ha)) (witHand_hand b (hval b hb)) hW
    rw [wit_mask a (hval a ha), wit_mask b (hval b hb)] at hm
    exact inj_of_nodup_map _ ws hnd a ha b hb hm
  have hwsnd : ws.Nodup := by
    have key : ∀ (l : List Nat), (l.map (fun u => wAll (mOnly u))).Nodup → l.Nodup := by
      intro l
      induction l with
      | nil => intro _; exact List.nodup_nil
      | cons a l ih =>
        intro h
        rw [List.map_cons, List.nodup_cons] at h
        rw [List.nodup_cons]
        exact ⟨fun hm => h.1 (List.mem_map.mpr ⟨a, hm, rfl⟩), ih h.2⟩
    exact key ws hnd
  have hbound : 7 ^ k ≤ 343 := by
    rcases (show k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 by omega) with rfl | rfl | rfl | rfl <;> decide
  obtain ⟨a, ha, b, hb, hab, he⟩ := pigeonhole (fun u => enc7 k (code u)) 343 ws hwsnd (by omega)
    (fun u hu => Nat.lt_of_lt_of_le (enc7_lt k _ (hcode_range u hu)) hbound)
  exact hab (hinj a ha b hb he)

end Tenpai
