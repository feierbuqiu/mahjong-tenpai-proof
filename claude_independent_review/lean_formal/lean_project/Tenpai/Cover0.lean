import Tenpai.Glue2

/-! # Helpers for the coverage proof -/

namespace Tenpai

/-! ## pigeonhole -/

theorem nodup_map_of_inj_on {α β : Type} (f : α → β) : ∀ (l : List α), l.Nodup →
    (∀ a ∈ l, ∀ b ∈ l, f a = f b → a = b) → (l.map f).Nodup
  | [], _, _ => List.nodup_nil
  | a :: l, hl, hinj => by
    rw [List.nodup_cons] at hl
    rw [List.map_cons, List.nodup_cons]
    refine ⟨?_, nodup_map_of_inj_on f l hl.2 (fun x hx y hy h => hinj x (List.mem_cons_of_mem _ hx) y
      (List.mem_cons_of_mem _ hy) h)⟩
    intro hm
    rw [List.mem_map] at hm
    obtain ⟨b, hb, he⟩ := hm
    have := hinj b (List.mem_cons_of_mem _ hb) a List.mem_cons_self he
    subst this
    exact hl.1 hb

/-- pigeonhole: more distinct items than boxes -/
theorem pigeonhole {α : Type} [DecidableEq α] (f : α → Nat) (n : Nat) (l : List α) (hl : l.Nodup)
    (hlen : n < l.length) (hf : ∀ a ∈ l, f a < n) : ∃ a ∈ l, ∃ b ∈ l, a ≠ b ∧ f a = f b := by
  apply Classical.byContradiction
  intro hno
  have hinj : ∀ a ∈ l, ∀ b ∈ l, f a = f b → a = b := by
    intro a ha b hb he
    exact Decidable.byContradiction fun hne => hno ⟨a, ha, b, hb, hne, he⟩
  have hnd := nodup_map_of_inj_on f l hl hinj
  have hsub : l.map f ⊆ List.range n := by
    intro x hx
    rw [List.mem_map] at hx
    obtain ⟨a, ha, rfl⟩ := hx
    exact List.mem_range.mpr (hf a ha)
  have := List.Nodup.length_le_of_subset hnd hsub
  rw [List.length_map, List.length_range] at this
  omega

/-! ## congruence of the loops -/

theorem orBelow_congr {f g : Nat → Nat} : ∀ {n}, (∀ i < n, f i = g i) → orBelow f n = orBelow g n
  | 0, _ => rfl
  | n + 1, h => by
    show Nat.lor (f n) (orBelow f n) = Nat.lor (g n) (orBelow g n)
    rw [h n (by omega), orBelow_congr (fun i hi => h i (by omega))]

theorem allBelow_congr {f g : Nat → Bool} : ∀ {n}, (∀ i < n, f i = g i) → allBelow f n = allBelow g n
  | 0, _ => rfl
  | n + 1, h => by
    show (f n && allBelow f n) = (g n && allBelow g n)
    rw [h n (by omega), allBelow_congr (fun i hi => h i (by omega))]

theorem lor_congr {a a' b b' : Nat} (h1 : a = a') (h2 : b = b') : Nat.lor a b = Nat.lor a' b' := by
  rw [h1, h2]

theorem wAll_congr (cv cv' : Nat → Nat) (h : ∀ k < 4, cv k = cv' k) : wAll cv = wAll cv' := by
  have hg : glue cv = glue cv' := by
    unfold glue; rw [h 0 (by omega), h 1 (by omega), h 2 (by omega), h 3 (by omega)]
  have hs : wStd cv = wStd cv' := by
    rw [wStd_eq, wStd_eq]
    unfold wStdP
    refine lor_congr (orBelow_congr fun x hx => ?_) (orBelow_congr fun x hx => orBelow_congr fun y hy => ?_)
    · rw [allBelow_congr (g := fun k => Nat.beq k x || cM k (cv' k)) (fun k hk => by rw [h k hk]), h x hx]
    · rw [allBelow_congr (g := fun k => Nat.beq k x || Nat.beq k y || cM k (cv' k)) (fun k hk => by rw [h k hk]),
        h x hx, h y hy]
  unfold wAll; rw [hs, hg]

theorem sel4_cv (cv : Nat → Nat) : ∀ k < 4, sel4 (cv 0) (cv 1) (cv 2) (cv 3) k = cv k := by
  intro k hk
  rcases (show k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 by omega) with rfl | rfl | rfl | rfl <;> rfl

/-! ## counting singles -/

theorem countBelow_split (q : Nat → Bool) (a : Nat) :
    ∀ b, countBelow q (a + b) = countBelow q a + countBelow (fun i => q (a + i)) b
  | 0 => rfl
  | b + 1 => by
    show Nat.add (countBelow q (a + b)) (cond (q (a + b)) 1 0) = _
    rw [countBelow_split q a b]
    show _ = countBelow q a + Nat.add (countBelow (fun i => q (a + i)) b) (cond (q (a + b)) 1 0)
    simp only [Nat.add_eq]
    omega

theorem countBelow_congr {f g : Nat → Bool} : ∀ {n}, (∀ i < n, f i = g i) → countBelow f n = countBelow g n
  | 0, _ => rfl
  | n + 1, h => by
    show Nat.add (countBelow f n) (cond (f n) 1 0) = Nat.add (countBelow g n) (cond (g n) 1 0)
    rw [h n (by omega), countBelow_congr (fun i hi => h i (by omega))]

theorem singles_sum (H : Counts) (hH : ∀ s, H s ≤ 4) :
    Nat.add (Nat.add (singles 9 (cvOf H 0)) (singles 9 (cvOf H 1))) (Nat.add (singles 9 (cvOf H 2)) (singles 7 (cvOf H 3)))
      = (List.finRange 34).countP (fun s => H s = 1) := by
  have hc : ∀ k, k < 4 → singles (catLen k) (cvOf H k) = countBelow (fun j => Nat.beq (extF H (9 * k + j)) 1) (catLen k) := by
    intro k hk
    unfold singles
    apply countBelow_congr
    intro j hj
    unfold cvOf catPk
    rw [fld_pkF _ _ (fun i _ => by have := catF_le4 H hH k i; omega), ite_eq_left hj]
    rfl
  have h0 := hc 0 (by omega); have h1 := hc 1 (by omega); have h2 := hc 2 (by omega); have h3 := hc 3 (by omega)
  simp only [catLen, show (0:Nat) < 3 from by decide, show (1:Nat) < 3 from by decide,
    show (2:Nat) < 3 from by decide, show ¬ ((3:Nat) < 3) from by decide, ite_true, ite_false] at h0 h1 h2 h3
  rw [h0, h1, h2, h3]
  have e : (List.finRange 34).countP (fun s => H s = 1) = countBelow (fun t => Nat.beq (extF H t) 1) 34 := by
    rw [← countP_finRange]
    congr 1
    funext s
    simp [extF, s.isLt, beq_decide]
  rw [e, show (34 : Nat) = 27 + 7 from rfl, countBelow_split, show (27 : Nat) = 18 + 9 from rfl, countBelow_split,
    show (18 : Nat) = 9 + 9 from rfl, countBelow_split]
  simp only [Nat.add_eq, Nat.mul_zero, Nat.zero_add, show 9 * 1 = 9 from rfl, show 9 * 2 = 9 + 9 from rfl,
    show 9 * 3 = 9 + 9 + 9 from rfl]
  omega

theorem shaped7_singles (H : Counts) (z : Tile) (h : Shaped7 H z) :
    (List.finRange 34).countP (fun s => H s = 1) = 1 := by
  rw [countP_eq_total]
  have : (fun s => if H s = 1 then 1 else 0) = fun s => if s = z then 1 else 0 := by
    funext s
    by_cases hs : s = z
    · subst hs; simp [h.1]
    · have := h.2.1 s hs
      have : ¬ H s = 1 := by omega
      simp [hs, this]
  rw [this, total_indicator]

/-! ## a category with one tile -/

theorem sumF_eq_zero (f : Nat → Nat) : ∀ n, sumF f n = 0 → ∀ i < n, f i = 0
  | 0, _, i, hi => absurd hi (by omega)
  | n + 1, h, i, hi => by
    rw [sumF_succ] at h
    by_cases hin : i = n
    · subst hin; omega
    · exact sumF_eq_zero f n (by omega) i (by omega)

theorem sumF_one (f : Nat → Nat) : ∀ n, sumF f n = 1 → ∃ j < n, f j = 1 ∧ ∀ i < n, i ≠ j → f i = 0
  | 0, h => by simp [sumF] at h
  | n + 1, h => by
    rw [sumF_succ] at h
    by_cases hn : f n = 0
    · obtain ⟨j, hj, h1, h0⟩ := sumF_one f n (by omega)
      refine ⟨j, by omega, h1, fun i hi hij => ?_⟩
      by_cases hin : i = n
      · subst hin; exact hn
      · exact h0 i (by omega) hij
    · have hs : sumF f n = 0 := by omega
      exact ⟨n, by omega, by omega, fun i hi hij => sumF_eq_zero f n hs i (by omega)⟩

/-! ## category masks -/

theorem testBit_catsExcept (x k : Nat) (hx : x < 4) : (catsExcept x).testBit k = true ↔ k < 4 ∧ k ≠ x := by
  unfold catsExcept
  show (15 ^^^ 1 <<< x).testBit k = true ↔ _
  rw [Nat.testBit_xor, Nat.one_shiftLeft, Nat.testBit_two_pow]
  have h15 : (15 : Nat).testBit k = decide (k < 4) := by
    rcases (show k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 ∨ 4 ≤ k by omega) with rfl | rfl | rfl | rfl | hk
    · rfl
    · rfl
    · rfl
    · rfl
    · rw [show decide (k < 4) = false by simp; omega]
      exact Nat.testBit_lt_two_pow (Nat.lt_of_lt_of_le (show (15:Nat) < 2 ^ 4 by decide)
        (Nat.pow_le_pow_right (by omega) hk))
  rw [h15]
  by_cases h1 : k < 4 <;> by_cases h2 : x = k <;> simp_all <;> omega

theorem testBit_catsExcept2 (x y k : Nat) (hx : x < 4) (hy : y < 4) (hxy : x ≠ y) :
    (catsExcept2 x y).testBit k = true ↔ k < 4 ∧ k ≠ x ∧ k ≠ y := by
  unfold catsExcept2
  show (catsExcept x ^^^ 1 <<< y).testBit k = true ↔ _
  rw [Nat.testBit_xor, Nat.one_shiftLeft, Nat.testBit_two_pow]
  have := testBit_catsExcept x k hx
  by_cases h2 : y = k
  · subst h2; simp only [decide_true]
    cases hb : (catsExcept x).testBit y <;> simp_all
  · simp only [h2, decide_false, Bool.xor_false]
    rw [this]; constructor
    · rintro ⟨a, b⟩; exact ⟨a, b, fun e => h2 e.symm⟩
    · rintro ⟨a, b, -⟩; exact ⟨a, b⟩

/-! ## packed sub-multisets -/

theorem small_hand (G : Counts) (hG : ∀ s, G s ≤ 4) : Small (pkF (extF G) 34) :=
  ⟨hand_lt G hG, fun t ht => hand_fld4 G hG t ht⟩

theorem sub_fld (G H : Counts) (hGH : ∀ s, G s ≤ H s) (hH : ∀ s, H s ≤ 4) (t : Nat) (_ht : t < 34) :
    fld (pkF (extF G) 34) t ≤ fld (pkF (extF H) 34) t := by
  rw [fld_hand G (fun s => Nat.le_trans (hGH s) (hH s)), fld_hand H hH]
  simp only [extF, _ht, dite_true]
  exact hGH _

end Tenpai
