import Tenpai.Std

/-!
# The full wait set as a computable 34-bit mask

`wAll cv` is computed from the four packed category vectors `cv 0 … cv 3` of a hand:
standard-form waits from the per-category tests, seven-pairs and thirteen-orphans waits
directly from the definitions.  `wAll_correct`: bit `t` of `wAll` is set iff `t ∈ W(H)`.
-/

namespace Tenpai

/-! ## more kernel loops -/

noncomputable def allBelow (f : Nat → Bool) (n : Nat) : Bool :=
  Nat.rec (motive := fun _ => Bool) true (fun i ih => f i && ih) n

noncomputable def countBelow (f : Nat → Bool) (n : Nat) : Nat :=
  Nat.rec (motive := fun _ => Nat) 0 (fun i ih => Nat.add ih (cond (f i) 1 0)) n

noncomputable def orBelow (f : Nat → Nat) (n : Nat) : Nat :=
  Nat.rec (motive := fun _ => Nat) 0 (fun i ih => Nat.lor (f i) ih) n

theorem allBelow_zero (f : Nat → Bool) : allBelow f 0 = true := rfl
theorem orBelow_zero (f : Nat → Nat) : orBelow f 0 = 0 := rfl

theorem testBit_lor' (a b i : Nat) : (Nat.lor a b).testBit i = (a.testBit i || b.testBit i) :=
  Nat.testBit_or a b i

theorem beq_decide (a b : Nat) : Nat.beq a b = decide (a = b) := by
  cases hb : Nat.beq a b
  · have : a ≠ b := fun e => by subst e; rw [Nat.beq_refl] at hb; exact Bool.noConfusion hb
    simp [this]
  · simp [Nat.eq_of_beq_eq_true hb]

theorem allBelow_iff (f : Nat → Bool) : ∀ n, allBelow f n = true ↔ ∀ i < n, f i = true
  | 0 => by rw [allBelow_zero]; simp
  | n + 1 => by
    show (f n && allBelow f n) = true ↔ _
    rw [Bool.and_eq_true, allBelow_iff f n]
    constructor
    · rintro ⟨h1, h2⟩ i hi
      by_cases hin : i = n
      · subst hin; exact h1
      · exact h2 i (by omega)
    · intro h; exact ⟨h n (by omega), fun i hi => h i (by omega)⟩

theorem testBit_orBelow (f : Nat → Nat) : ∀ n i, (orBelow f n).testBit i = true ↔ ∃ x < n, (f x).testBit i = true
  | 0, i => by rw [orBelow_zero]; simp
  | n + 1, i => by
    show (Nat.lor (f n) (orBelow f n)).testBit i = true ↔ _
    rw [testBit_lor', Bool.or_eq_true, testBit_orBelow f n i]
    constructor
    · rintro (h | ⟨x, hx, h⟩)
      · exact ⟨n, by omega, h⟩
      · exact ⟨x, by omega, h⟩
    · rintro ⟨x, hx, h⟩
      by_cases hxn : x = n
      · subst hxn; exact Or.inl h
      · exact Or.inr ⟨x, by omega, h⟩

theorem countBelow_range (q : Nat → Bool) : ∀ n, (List.range n).countP q = countBelow q n
  | 0 => rfl
  | n + 1 => by
    rw [List.range_succ, List.countP_append, countBelow_range q n]
    show _ = Nat.add (countBelow q n) (cond (q n) 1 0)
    cases h : q n <;> simp [h]

theorem map_val_finRange (n : Nat) : (List.finRange n).map Fin.val = List.range n := by
  apply List.ext_getElem
  · simp
  · intro i h1 h2
    simp [List.getElem_finRange]

theorem countP_finRange (q : Nat → Bool) (n : Nat) :
    (List.finRange n).countP (fun s => q s.val) = countBelow q n := by
  rw [← countBelow_range, ← map_val_finRange, List.countP_map]
  rfl

/-! ## the global packed hand -/

/-- glue four category vectors into one 34-field vector -/
def glue (cv : Nat → Nat) : Nat :=
  Nat.add (cv 0) (Nat.add (Nat.shiftLeft (cv 1) 36) (Nat.add (Nat.shiftLeft (cv 2) 72) (Nat.shiftLeft (cv 3) 108)))

/-- the category vectors of a count function -/
def cvOf (F : Counts) : Nat → Nat := fun k => catPk (extF F) k

theorem glue_cvOf (F : Counts) : glue (cvOf F) = pkF (extF F) 34 := by
  have e0 : cvOf F 0 = pkF (extF F) 9 := pkF_congr (fun j _ => by simp [catF])
  have e1 : cvOf F 1 = pkF (fun i => extF F (9 + i)) 9 := pkF_congr (fun j _ => by simp [catF])
  have e2 : cvOf F 2 = pkF (fun i => extF F (18 + i)) 9 := pkF_congr (fun j _ => by simp [catF])
  have e3 : cvOf F 3 = pkF (fun i => extF F (27 + i)) 7 := pkF_congr (fun j _ => by simp [catF])
  have s2 := pkF_split (extF F) 9 9
  have s3 := pkF_split (extF F) 18 9
  have s4 := pkF_split (extF F) 27 7
  have p9 : (16 : Nat) ^ 9 = 68719476736 := by decide
  have p18 : (16 : Nat) ^ 18 = 4722366482869645213696 := by decide
  have p27 : (16 : Nat) ^ 27 = 324518553658426726783156020576256 := by decide
  rw [p9] at s2; rw [p18] at s3; rw [p27] at s4
  unfold glue
  rw [e0, e1, e2, e3]
  show pkF (extF F) 9 + (pkF (fun i => extF F (9 + i)) 9 <<< 36 +
    (pkF (fun i => extF F (18 + i)) 9 <<< 72 + pkF (fun i => extF F (27 + i)) 7 <<< 108)) = _
  rw [Nat.shiftLeft_eq, Nat.shiftLeft_eq, Nat.shiftLeft_eq]
  have q36 : (2 : Nat) ^ 36 = 68719476736 := by decide
  have q72 : (2 : Nat) ^ 72 = 4722366482869645213696 := by decide
  have q108 : (2 : Nat) ^ 108 = 324518553658426726783156020576256 := by decide
  rw [q36, q72, q108, show (34 : Nat) = 27 + 7 from rfl, s4, show (27 : Nat) = 18 + 9 from rfl, s3,
    show (18 : Nat) = 9 + 9 from rfl, s2]
  omega

theorem fld_hand (F : Counts) (hF : ∀ s, F s ≤ 4) (t : Nat) :
    fld (pkF (extF F) 34) t = extF F t := by
  rw [fld_pkF _ _ (fun i _ => extF_lt F hF i)]
  split
  · rfl
  · simp only [extF]; split <;> omega

/-! ## orphans -/

def isOrphB (t : Nat) : Bool :=
  (Nat.blt t 27 && (Nat.beq (Nat.mod t 9) 0 || Nat.beq (Nat.mod t 9) 8)) || Nat.ble 27 t

theorem isOrphB_iff (t : Tile) : isOrphB t.val = true ↔ IsOrphan t := by
  unfold isOrphB IsOrphan
  simp only [Bool.or_eq_true, Bool.and_eq_true, Nat.blt_eq, Nat.beq_eq, Nat.ble_eq]
  rfl

/-! ## seven pairs -/

/-- `g` (34 fields) is seven distinct pairs -/
noncomputable def sevenB (g : Nat) : Bool :=
  allBelow (fun s => Nat.beq (fld g s) 0 || Nat.beq (fld g s) 2) 34 &&
  Nat.beq (countBelow (fun s => Nat.beq (fld g s) 2) 34) 7

theorem nodup_filter {α : Type} (p : α → Bool) (l : List α) (h : l.Nodup) : (l.filter p).Nodup :=
  List.Nodup.sublist List.filter_sublist h

theorem isSevenPairs_iff (G : Counts) :
    IsSevenPairs G ↔ (∀ s, G s = 0 ∨ G s = 2) ∧ (List.finRange 34).countP (fun s => G s = 2) = 7 := by
  constructor
  · rintro ⟨S, hS, hl, he⟩
    refine ⟨fun s => by rw [he s]; split <;> simp, ?_⟩
    rw [List.countP_eq_length_filter, ← hl]
    apply List.Perm.length_eq
    rw [List.perm_ext_iff_of_nodup (nodup_filter _ _ (List.nodup_finRange 34)) hS]
    intro a
    rw [List.mem_filter, he a]
    simp only [List.mem_finRange, true_and, decide_eq_true_eq]
    split <;> simp_all
  · rintro ⟨h02, hc⟩
    refine ⟨(List.finRange 34).filter (fun s => G s = 2), nodup_filter _ _ (List.nodup_finRange 34),
      by rw [← List.countP_eq_length_filter, hc], ?_⟩
    intro s
    by_cases hs : G s = 2
    · have : s ∈ (List.finRange 34).filter (fun s => G s = 2) :=
        List.mem_filter.mpr ⟨List.mem_finRange s, by simp [hs]⟩
      simp [this, hs]
    · have : s ∉ (List.finRange 34).filter (fun s => G s = 2) := fun h =>
        hs (by simpa using (List.mem_filter.mp h).2)
      simp only [this, ite_false]
      rcases h02 s with h | h
      · exact h
      · exact absurd h hs

theorem sevenB_iff (G : Counts) (hG : ∀ s, G s ≤ 4) :
    sevenB (pkF (extF G) 34) = true ↔ IsSevenPairs G := by
  rw [isSevenPairs_iff]
  unfold sevenB
  rw [Bool.and_eq_true, allBelow_iff, Nat.beq_eq]
  have hf := fld_hand G hG
  have e : (List.finRange 34).countP (fun s => G s = 2) =
      countBelow (fun s => Nat.beq (fld (pkF (extF G) 34) s) 2) 34 := by
    rw [← countP_finRange]
    congr 1
    funext s
    rw [hf]
    simp only [extF, s.isLt, dite_true, beq_decide]
  rw [e]
  apply and_congr_left
  intro _
  constructor
  · intro h s
    have := h s.val s.isLt
    rw [hf] at this
    simp only [extF, s.isLt, dite_true, Bool.or_eq_true, Nat.beq_eq] at this
    exact this
  · intro h i hi
    rw [hf]
    simp only [extF, hi, dite_true, Bool.or_eq_true, Nat.beq_eq]
    exact h ⟨i, hi⟩

/-! ## thirteen orphans -/

/-- `g` (34 fields) is a thirteen-orphans hand, written as a bounded search over `o` -/
noncomputable def kokB (g : Nat) : Bool :=
  anyBelow (fun o => isOrphB o && Nat.beq (fld g o) 2 && allBelow (fun s =>
    Nat.beq (fld g s) (Nat.add (cond (isOrphB s) 1 0) (cond (Nat.beq s o) 1 0))) 34) 34

theorem kokB_iff (G : Counts) (hG : ∀ s, G s ≤ 4) :
    kokB (pkF (extF G) 34) = true ↔ IsKokushi G := by
  unfold kokB IsKokushi
  rw [anyBelow_iff]
  have hf := fld_hand G hG
  constructor
  · rintro ⟨o, ho, h⟩
    rw [Bool.and_eq_true, Bool.and_eq_true, allBelow_iff] at h
    refine ⟨⟨o, ho⟩, (isOrphB_iff ⟨o, ho⟩).mp h.1.1, fun s => ?_⟩
    have := h.2 s.val s.isLt
    rw [hf, Nat.beq_eq] at this
    simp only [extF, s.isLt, dite_true] at this
    rw [this]
    congr 1
    · cases hs : isOrphB s.val
      · have : ¬ IsOrphan s := fun h' => by rw [← isOrphB_iff] at h'; simp_all
        simp [this]
      · have : IsOrphan s := (isOrphB_iff s).mp hs
        simp [this]
    · cases hs : Nat.beq s.val o
      · have : s ≠ ⟨o, ho⟩ := fun e => by subst e; simp at hs
        simp [this]
      · have : s = ⟨o, ho⟩ := Fin.ext (Nat.eq_of_beq_eq_true hs)
        simp [this]
  · rintro ⟨o, ho, h⟩
    refine ⟨o.val, o.isLt, ?_⟩
    rw [Bool.and_eq_true, Bool.and_eq_true, allBelow_iff]
    have hoo : fld (pkF (extF G) 34) o.val = 2 := by
      rw [hf]; simp only [extF, o.isLt, dite_true]; rw [h o]; simp [ho]
    refine ⟨⟨(isOrphB_iff o).mpr ho, by rw [hoo]; rfl⟩, fun i hi => ?_⟩
    rw [hf, Nat.beq_eq]
    simp only [extF, hi, dite_true]
    rw [h ⟨i, hi⟩]
    congr 1
    · cases hs : isOrphB i
      · have : ¬ IsOrphan ⟨i, hi⟩ := fun h' => by rw [← isOrphB_iff] at h'; simp_all
        simp [this]
      · have : IsOrphan ⟨i, hi⟩ := (isOrphB_iff ⟨i, hi⟩).mp hs
        simp [this]
    · cases hs : Nat.beq i o.val
      · have : (⟨i, hi⟩ : Tile) ≠ o := fun e => by subst e; simp at hs
        simp [this]
      · have : (⟨i, hi⟩ : Tile) = o := Fin.ext (Nat.eq_of_beq_eq_true hs)
        simp [this]

/-! ## standard form, as category masks -/

/-- standard-form waits from the category tests (form used in proofs) -/
noncomputable def wStdP (cv : Nat → Nat) : Nat :=
  Nat.lor
    (orBelow (fun x => cond (allBelow (fun k => Nat.beq k x || cM k (cv k)) 4)
        (Nat.shiftLeft (cWP x (cv x)) (Nat.mul 9 x)) 0) 4)
    (orBelow (fun x => orBelow (fun y =>
        cond (!(Nat.beq y x) && cP y (cv y) && allBelow (fun k => Nat.beq k x || Nat.beq k y || cM k (cv k)) 4)
          (Nat.shiftLeft (cWM x (cv x)) (Nat.mul 9 x)) 0) 4) 4)

/-- standard-form waits, as evaluated by the kernel: every category test is memoised by value -/
noncomputable def wStd (cv : Nat → Nat) : Nat :=
  Nat.lor
    (orBelow (fun x => cond (allBelow (fun k => Nat.beq k x || force (cv k) (cM k)) 4)
        (Nat.shiftLeft (force (cv x) (cWP x)) (Nat.mul 9 x)) 0) 4)
    (orBelow (fun x => orBelow (fun y =>
        cond (!(Nat.beq y x) && force (cv y) (cP y) &&
              allBelow (fun k => Nat.beq k x || Nat.beq k y || force (cv k) (cM k)) 4)
          (Nat.shiftLeft (force (cv x) (cWM x)) (Nat.mul 9 x)) 0) 4) 4)

theorem wStd_eq (cv : Nat → Nat) : wStd cv = wStdP cv := by
  unfold wStd wStdP; simp only [force_eq]

/-- the full wait mask; a seven-pairs wait can only be the single tile, a thirteen-orphans wait
    only a terminal or honour, so these cheap tests guard the expensive ones -/
noncomputable def wAll (cv : Nat → Nat) : Nat :=
  Nat.lor (wStd cv) (Nat.lor
    (maskBelow (fun t => Nat.blt (fld (glue cv) t) 4 && Nat.beq (fld (glue cv) t) 1 &&
       force (Nat.add (glue cv) (Nat.shiftLeft 1 (Nat.mul 4 t))) sevenB) 34)
    (maskBelow (fun t => Nat.blt (fld (glue cv) t) 4 && isOrphB t &&
       force (Nat.add (glue cv) (Nat.shiftLeft 1 (Nat.mul 4 t))) kokB) 34))

theorem testBit_shift9 (m x t : Nat) :
    (Nat.shiftLeft m (Nat.mul 9 x)).testBit t = (decide (9 * x ≤ t) && m.testBit (t - 9 * x)) := by
  show (m <<< (9 * x)).testBit t = _
  rw [Nat.testBit_shiftLeft]

theorem testBit_cWP (k v j : Nat) :
    (cWP k v).testBit j = true ↔ j < catLen k ∧ fld v j < 4 ∧ cP k (v + 16 ^ j) = true :=
  testBit_wpL _ _ _ _

theorem testBit_cWM (k v j : Nat) :
    (cWM k v).testBit j = true ↔ j < catLen k ∧ fld v j < 4 ∧ cM k (v + 16 ^ j) = true :=
  testBit_wmL _ _ _ _

theorem cat_of_offset (x t : Nat) (hx : x < 4) (h1 : 9 * x ≤ t) (h2 : t - 9 * x < catLen x) : t / 9 = x := by
  unfold catLen at h2; split at h2 <;> omega

theorem testBit_wStd (cv : Nat → Nat) (t : Nat) (ht : t < 34) :
    (wStd cv).testBit t = true ↔
      fld (cv (t / 9)) (t % 9) < 4 ∧
      ((cP (t / 9) (cv (t / 9) + 16 ^ (t % 9)) = true ∧ ∀ k < 4, k ≠ t / 9 → cM k (cv k) = true) ∨
       (cM (t / 9) (cv (t / 9) + 16 ^ (t % 9)) = true ∧ ∃ y < 4, y ≠ t / 9 ∧ cP y (cv y) = true ∧
          ∀ k < 4, k ≠ t / 9 → k ≠ y → cM k (cv k) = true)) := by
  have hx : t / 9 < 4 := by omega
  have hj : t % 9 < catLen (t / 9) := by unfold catLen; split <;> omega
  have e9 : t - 9 * (t / 9) = t % 9 := by omega
  rw [wStd_eq]
  unfold wStdP
  rw [testBit_lor', Bool.or_eq_true, testBit_orBelow, testBit_orBelow]
  constructor
  · rintro (⟨x, hx4, h⟩ | ⟨x, hx4, h⟩)
    · cases hc : allBelow (fun k => Nat.beq k x || cM k (cv k)) 4
      · simp [hc] at h
      · rw [hc, Bool.cond_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq] at h
        obtain ⟨h1, h2⟩ := h
        rw [testBit_cWP] at h2
        have hxt := cat_of_offset x t hx4 h1 h2.1
        subst hxt
        rw [e9] at h2
        refine ⟨h2.2.1, Or.inl ⟨h2.2.2, fun k hk hne => ?_⟩⟩
        have := (allBelow_iff _ 4).mp hc k hk
        simp [Nat.beq_eq, hne] at this
        exact this
    · rw [testBit_orBelow] at h
      obtain ⟨y, hy4, h⟩ := h
      cases hc : (!(Nat.beq y x) && cP y (cv y) && allBelow (fun k => Nat.beq k x || Nat.beq k y || cM k (cv k)) 4)
      · simp [hc] at h
      · rw [hc, Bool.cond_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq] at h
        obtain ⟨h1, h2⟩ := h
        rw [testBit_cWM] at h2
        have hxt := cat_of_offset x t hx4 h1 h2.1
        subst hxt
        rw [e9] at h2
        simp only [Bool.and_eq_true, Bool.not_eq_true', beq_decide, decide_eq_false_iff_not] at hc
        obtain ⟨⟨hyx, hP⟩, hall⟩ := hc
        refine ⟨h2.2.1, Or.inr ⟨h2.2.2, y, hy4, by
          intro e; apply hyx; simp [e], hP, fun k hk h1' h2' => ?_⟩⟩
        have := (allBelow_iff _ 4).mp hall k hk
        simp [h1', h2'] at this
        exact this
  · rintro ⟨h4, (⟨hP, hM⟩ | ⟨hM, y, hy4, hyx, hP, hrest⟩)⟩
    · left
      refine ⟨t / 9, hx, ?_⟩
      have hc : allBelow (fun k => Nat.beq k (t / 9) || cM k (cv k)) 4 = true := by
        rw [allBelow_iff]
        intro k hk
        by_cases hkx : k = t / 9
        · simp [hkx]
        · simp [hM k hk hkx]
      rw [hc, Bool.cond_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq, testBit_cWP, e9]
      exact ⟨by omega, hj, h4, hP⟩
    · right
      refine ⟨t / 9, hx, ?_⟩
      rw [testBit_orBelow]
      refine ⟨y, hy4, ?_⟩
      have hc : (!(Nat.beq y (t / 9)) && cP y (cv y) &&
          allBelow (fun k => Nat.beq k (t / 9) || Nat.beq k y || cM k (cv k)) 4) = true := by
        simp only [Bool.and_eq_true, Bool.not_eq_true', beq_decide, decide_eq_false_iff_not]
        refine ⟨⟨hyx, hP⟩, ?_⟩
        rw [allBelow_iff]
        intro k hk
        by_cases h1 : k = t / 9
        · simp [h1]
        · by_cases h2 : k = y
          · simp [h2]
          · simp [hrest k hk h1 h2]
      rw [hc, Bool.cond_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq, testBit_cWM, e9]
      exact ⟨by omega, hj, h4, hM⟩

/-! ## correctness of the full mask -/

theorem pkF_extF_addTile (H : Counts) (t : Tile) :
    pkF (extF H) 34 + 16 ^ t.val = pkF (extF (addTile H t)) 34 := by
  rw [pkF_add_single _ _ _ t.isLt]
  apply pkF_congr
  intro i hi
  simp only [extF, hi, dite_true, addTile]
  by_cases h : i = t.val
  · subst h; simp
  · rw [ite_eq_right h, ite_eq_right]
    intro e; exact h (congrArg Fin.val e)

theorem addTile_lt (H : Counts) (hH : ∀ s, H s ≤ 4) (t : Tile) (s : Tile) : addTile H t s ≤ 5 := by
  unfold addTile; split <;> have := hH s <;> omega

theorem seven_single (H : Counts) (t : Tile) (h : IsSevenPairs (addTile H t)) : H t = 1 := by
  rw [isSevenPairs_iff] at h
  have := h.1 t
  simp only [addTile, ite_true] at this
  omega

theorem kok_orphan (H : Counts) (t : Tile) (h : IsKokushi (addTile H t)) : IsOrphan t := by
  obtain ⟨o, ho, he⟩ := h
  have := he t
  simp only [addTile, ite_true] at this
  by_cases hto : IsOrphan t
  · exact hto
  · by_cases e : t = o
    · subst e; exact ho
    · simp [hto, e] at this

theorem wAll_correct (H : Counts) (hH : IsHand H) (t : Tile) :
    (wAll (cvOf H)).testBit t.val = true ↔ W H t := by
  have hle := hH.2
  have ht := t.isLt
  have hfx : fld (cvOf H (t.val / 9)) (t.val % 9) = H t := fld_catPk H hle t
  have hglue : glue (cvOf H) = pkF (extF H) 34 := glue_cvOf H
  have hfg : fld (glue (cvOf H)) t.val = H t := by
    rw [hglue, fld_hand H hle]; simp [extF, ht]
  have hadd : Nat.add (glue (cvOf H)) (Nat.shiftLeft 1 (Nat.mul 4 t.val)) = pkF (extF (addTile H t)) 34 := by
    rw [shiftLeft_four, Nat.one_mul, hglue, show Nat.add (pkF (extF H) 34) (16 ^ t.val) =
      pkF (extF H) 34 + 16 ^ t.val from rfl, pkF_extF_addTile]
  unfold wAll
  rw [testBit_lor', testBit_lor', testBit_maskBelow, testBit_maskBelow, Bool.or_eq_true,
    Bool.or_eq_true, testBit_wStd _ _ ht]
  simp only [ht, decide_true, Bool.true_and, Bool.and_eq_true, Nat.blt_eq, Nat.beq_eq, hfx, hfg,
    force_eq, hadd, isOrphB_iff]
  -- the three shapes
  unfold W IsWinning
  constructor
  · rintro (⟨h4, hstd⟩ | ⟨⟨h4, -⟩, h7⟩ | ⟨⟨h4, -⟩, hk⟩)
    · refine ⟨h4, addTile_le H hle t h4, Or.inl ?_⟩
      rw [std_wait_iff H hH t h4]
      exact hstd
    · exact ⟨h4, addTile_le H hle t h4, Or.inr (Or.inl ((sevenB_iff _ (addTile_le H hle t h4)).mp h7))⟩
    · exact ⟨h4, addTile_le H hle t h4, Or.inr (Or.inr ((kokB_iff _ (addTile_le H hle t h4)).mp hk))⟩
  · rintro ⟨h4, -, hstd | h7 | hk⟩
    · left
      exact ⟨h4, (std_wait_iff H hH t h4).mp hstd⟩
    · right; left
      exact ⟨⟨h4, seven_single H t h7⟩, (sevenB_iff _ (addTile_le H hle t h4)).mpr h7⟩
    · right; right
      exact ⟨⟨h4, kok_orphan H t hk⟩, (kokB_iff _ (addTile_le H hle t h4)).mpr hk⟩

end Tenpai
