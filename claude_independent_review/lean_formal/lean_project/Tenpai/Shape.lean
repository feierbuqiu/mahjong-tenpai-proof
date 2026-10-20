import Tenpai.Waits

/-!
# Shapes of tenpai hands

* category sizes mod 3 for meld / pair+meld vectors and for the two kinds of wait masks;
* the total of a hand is the sum of its four category sizes;
* a standard wait forces one of two patterns (one active category with remainder 1, or two
  active categories with remainder 2), and in each pattern the standard waits are exactly the
  bits of one or two category masks.
-/

namespace Tenpai

/-! ## sums -/

theorem sumF_succ (f : Nat → Nat) (n : Nat) : sumF f (n + 1) = sumF f n + f n := rfl

theorem sumF_congr {f g : Nat → Nat} : ∀ {n}, (∀ j < n, f j = g j) → sumF f n = sumF g n
  | 0, _ => rfl
  | n + 1, h => by rw [sumF_succ, sumF_succ, sumF_congr (fun j hj => h j (by omega)), h n (by omega)]

theorem sumF_add (f g : Nat → Nat) : ∀ n, sumF (fun j => f j + g j) n = sumF f n + sumF g n
  | 0 => rfl
  | n + 1 => by rw [sumF_succ, sumF_succ, sumF_succ, sumF_add f g n]; omega

theorem sumF_mul (c : Nat) (f : Nat → Nat) : ∀ n, sumF (fun j => c * f j) n = c * sumF f n
  | 0 => rfl
  | n + 1 => by rw [sumF_succ, sumF_succ, sumF_mul c f n, Nat.mul_add]

theorem sumF_split (f : Nat → Nat) (a : Nat) : ∀ b, sumF f (a + b) = sumF f a + sumF (fun i => f (a + i)) b
  | 0 => rfl
  | b + 1 => by rw [← Nat.add_assoc, sumF_succ, sumF_split f a b, sumF_succ]; omega

theorem sumF_single (j : Nat) : ∀ n, j < n → sumF (fun i => if i = j then 1 else 0) n = 1
  | 0, h => absurd h (by omega)
  | n + 1, h => by
    rw [sumF_succ]
    by_cases hj : j = n
    · subst hj
      rw [sumF_congr (g := fun _ => 0) (fun i hi => by simp; omega)]
      have : ∀ m, sumF (fun _ => 0) m = 0 := by
        intro m; induction m with
        | zero => rfl
        | succ m ih => rw [sumF_succ, ih]
      simp [this]
    · rw [sumF_single j n (by omega)]; simp [show n ≠ j from fun e => hj e.symm]

/-- the coverage by sequences sums to twice the number of sequences, when sequences fit -/
theorem sumF_seqCov (sq : Nat → Nat) : ∀ n, sumF (seqCov sq) n = sumF sq (n - 1) + sumF sq (n - 2)
  | 0 => rfl
  | n + 1 => by
    rw [sumF_succ, sumF_seqCov sq n]
    simp only [seqCov]
    rcases (show n = 0 ∨ n = 1 ∨ 2 ≤ n by omega) with rfl | rfl | h
    · rfl
    · simp [sumF]
    · rw [ite_eq_left (by omega), ite_eq_left (by omega)]
      rw [show n + 1 - 1 = (n - 1) + 1 by omega, show n + 1 - 2 = (n - 2) + 1 by omega, sumF_succ, sumF_succ]
      omega

theorem sumF_zero_tail (f : Nat → Nat) (n m : Nat) (h : ∀ j, m ≤ j → j < n → f j = 0) (hmn : m ≤ n) :
    sumF f n = sumF f m := by
  induction n with
  | zero => have : m = 0 := by omega
            subst this; rfl
  | succ n ih =>
    by_cases hm : m = n + 1
    · subst hm; rfl
    · rw [sumF_succ, h n (by omega) (by omega), ih (fun j h1 h2 => h j h1 (by omega)) (by omega), Nat.add_zero]

theorem localDec_sum (w : Nat → Nat) (lim n : Nat) (hl : lim = 0 ∨ lim + 2 ≤ n) (hd : LocalDec w lim n) :
    sumF w n % 3 = 0 := by
  obtain ⟨tr, sq, hsq, he⟩ := hd
  have e1 : sumF w n = sumF (fun i => 3 * tr i + (sq i + seqCov sq i)) n :=
    sumF_congr (fun i hi => by rw [he i hi]; omega)
  rw [e1, sumF_add, sumF_mul, sumF_add, sumF_seqCov]
  have z : ∀ j, (if lim = 0 then 0 else n - 2) ≤ j → sq j = 0 := by
    intro j hj
    exact Decidable.byContradiction fun h => by
      have := hsq j h; split at hj <;> omega
  have a1 : sumF sq (n - 1) = sumF sq n :=
    (sumF_zero_tail sq n (n - 1) (fun j h1 _ => z j (by split <;> omega)) (by omega)).symm
  have a2 : sumF sq (n - 2) = sumF sq n :=
    (sumF_zero_tail sq n (n - 2) (fun j h1 _ => z j (by split <;> omega)) (by omega)).symm
  rw [a1, a2]
  omega

/-! ## sizes of category vectors -/

/-- number of tiles of a local packed vector -/
noncomputable def csize (k v : Nat) : Nat := sumF (fld v) (catLen k)

theorem isM_pkF (k : Nat) (f : Nat → Nat) (hf : ∀ j < catLen k, f j < 16) :
    cM k (pkF f (catLen k)) = true ↔ LocalDec f (catLim k) (catLen k) := by
  unfold cM isM
  rw [grW_congr (v := f) (catLim k) (catLen k) 0 0 0 (fun i _ hi => by
    rw [fld_pkF _ _ hf, ite_eq_left (by omega)])]
  exact grW_correct _ _ _ (catLim_ok k)

theorem csize_pkF (k : Nat) (f : Nat → Nat) (hf : ∀ j < catLen k, f j < 16) :
    csize k (pkF f (catLen k)) = sumF f (catLen k) :=
  sumF_congr (fun j hj => by rw [fld_pkF _ _ hf, ite_eq_left hj])

theorem cM_size (k : Nat) (f : Nat → Nat) (hf : ∀ j < catLen k, f j < 16)
    (h : cM k (pkF f (catLen k)) = true) : sumF f (catLen k) % 3 = 0 :=
  localDec_sum f _ _ (catLim_ok k) ((isM_pkF k f hf).mp h)

theorem cP_size (k : Nat) (f : Nat → Nat) (hf : ∀ j < catLen k, f j ≤ 4)
    (h : cP k (pkF f (catLen k)) = true) : sumF f (catLen k) % 3 = 2 := by
  unfold cP at h
  rw [isP_iff] at h
  obtain ⟨q, hq, h2, hm⟩ := h
  have hfq : 2 ≤ f q := by rw [fld_pkF _ _ (fun i hi => by have := hf i hi; omega), ite_eq_left hq] at h2; exact h2
  rw [pkF_sub_pair _ _ _ hq hfq] at hm
  have := cM_size k _ (fun j hj => by have := hf j hj; split <;> omega) hm
  have e : sumF f (catLen k) = sumF (fun i => if i = q then f i - 2 else f i) (catLen k) + 2 := by
    have : sumF f (catLen k) = sumF (fun i => (if i = q then f i - 2 else f i) + 2 * (if i = q then 1 else 0))
        (catLen k) := sumF_congr (fun j _ => by split <;> simp_all <;> omega)
    rw [this, sumF_add, sumF_mul, sumF_single q _ hq]
  omega

theorem wpBit_size (k : Nat) (f : Nat → Nat) (hf : ∀ j < catLen k, f j ≤ 4) (j : Nat)
    (h : (cWP k (pkF f (catLen k))).testBit j = true) : sumF f (catLen k) % 3 = 1 := by
  rw [testBit_cWP] at h
  obtain ⟨hj, h4, hp⟩ := h
  have hfj : f j < 4 := by rw [fld_pkF _ _ (fun i hi => by have := hf i hi; omega), ite_eq_left hj] at h4; exact h4
  rw [pkF_add_single _ _ _ hj] at hp
  have := cP_size k _ (fun i hi => by have := hf i hi; split <;> (try subst_vars) <;> omega) hp
  have e : sumF (fun i => if i = j then f i + 1 else f i) (catLen k) = sumF f (catLen k) + 1 := by
    have : sumF (fun i => if i = j then f i + 1 else f i) (catLen k) =
        sumF (fun i => f i + (if i = j then 1 else 0)) (catLen k) := sumF_congr (fun i _ => by split <;> simp_all)
    rw [this, sumF_add, sumF_single j _ hj]
  omega

theorem wmBit_size (k : Nat) (f : Nat → Nat) (hf : ∀ j < catLen k, f j ≤ 4) (j : Nat)
    (h : (cWM k (pkF f (catLen k))).testBit j = true) : sumF f (catLen k) % 3 = 2 := by
  rw [testBit_cWM] at h
  obtain ⟨hj, h4, hm⟩ := h
  have hfj : f j < 4 := by rw [fld_pkF _ _ (fun i hi => by have := hf i hi; omega), ite_eq_left hj] at h4; exact h4
  rw [pkF_add_single _ _ _ hj] at hm
  have := cM_size k _ (fun i hi => by have := hf i hi; split <;> (try subst_vars) <;> omega) hm
  have e : sumF (fun i => if i = j then f i + 1 else f i) (catLen k) = sumF f (catLen k) + 1 := by
    have : sumF (fun i => if i = j then f i + 1 else f i) (catLen k) =
        sumF (fun i => f i + (if i = j then 1 else 0)) (catLen k) := sumF_congr (fun i _ => by split <;> simp_all)
    rw [this, sumF_add, sumF_single j _ hj]
  omega

/-! ## hands: category sizes -/

/-- size of category `k` of a hand -/
noncomputable def hsize (H : Counts) (k : Nat) : Nat := sumF (catF (extF H) k) (catLen k)

theorem sum_range_eq (f : Nat → Nat) : ∀ n, ((List.range n).map f).sum = sumF f n
  | 0 => rfl
  | n + 1 => by rw [List.range_succ, List.map_append, List.sum_append, sum_range_eq f n, sumF_succ]; simp

theorem sum_finRange_eq (f : Nat → Nat) (n : Nat) : ((List.finRange n).map (fun s => f s.val)).sum = sumF f n := by
  have : (List.finRange n).map (fun s => f s.val) = (List.range n).map f := by
    rw [← map_val_finRange, List.map_map]; rfl
  rw [this, sum_range_eq]

theorem total_eq_sizes (H : Counts) :
    total H = hsize H 0 + hsize H 1 + hsize H 2 + hsize H 3 := by
  have e : total H = sumF (extF H) 34 := by
    unfold total
    rw [← sum_finRange_eq]
    congr 1
  rw [e, show (34 : Nat) = 27 + 7 from rfl, sumF_split, show (27 : Nat) = 18 + 9 from rfl, sumF_split,
    show (18 : Nat) = 9 + 9 from rfl, sumF_split]
  unfold hsize catF catLen
  simp only [show (0 : Nat) < 3 from by decide, show (1 : Nat) < 3 from by decide,
    show (2 : Nat) < 3 from by decide, show ¬ ((3 : Nat) < 3) from by decide, ite_true, ite_false]
  have h0 : sumF (fun j => extF H (9 * 0 + j)) 9 = sumF (extF H) 9 := sumF_congr (fun j _ => by simp)
  have h1 : sumF (fun j => extF H (9 * 1 + j)) 9 = sumF (fun i => extF H (9 + i)) 9 := sumF_congr (fun j _ => by simp)
  have h2 : sumF (fun j => extF H (9 * 2 + j)) 9 = sumF (fun i => extF H (9 + 9 + i)) 9 := sumF_congr (fun j _ => by simp)
  have h3 : sumF (fun j => extF H (9 * 3 + j)) 7 = sumF (fun i => extF H (9 + 9 + 9 + i)) 7 := sumF_congr (fun j _ => by simp)
  rw [h0, h1, h2, h3]

theorem cv_pkF (H : Counts) (k : Nat) : cvOf H k = pkF (catF (extF H) k) (catLen k) := rfl

theorem catF_le4 (H : Counts) (hH : ∀ s, H s ≤ 4) (k j : Nat) : catF (extF H) k j ≤ 4 := by
  simp only [catF, extF]; split
  · exact hH _
  · omega

/-! ## the two standard patterns -/

/-- pattern (a): one active category `x` -/
def PatA (H : Counts) (x : Nat) : Prop :=
  x < 4 ∧ (∀ k < 4, k ≠ x → cM k (cvOf H k) = true) ∧ cWP x (cvOf H x) ≠ 0

/-- pattern (b): two active categories `x ≠ y`, `y` holding the pair -/
def PatB (H : Counts) (x y : Nat) : Prop :=
  x < 4 ∧ y < 4 ∧ x ≠ y ∧ cP y (cvOf H y) = true ∧ (∀ k < 4, k ≠ x → k ≠ y → cM k (cvOf H k) = true) ∧
    cWM x (cvOf H x) ≠ 0

theorem ne_zero_of_testBit {m j : Nat} (h : m.testBit j = true) : m ≠ 0 := by
  intro e; subst e; simp at h

theorem testBit_of_ne_zero {m : Nat} (h : m ≠ 0) : ∃ j, m.testBit j = true :=
  Nat.exists_testBit_of_ne_zero h

section sizes
variable (H : Counts) (hH : IsHand H)
include hH

theorem cM_mod (k : Nat) (h : cM k (cvOf H k) = true) : hsize H k % 3 = 0 :=
  cM_size k _ (fun j _ => by have := catF_le4 H hH.2 k j; omega) h

theorem cP_mod (k : Nat) (h : cP k (cvOf H k) = true) : hsize H k % 3 = 2 :=
  cP_size k _ (fun j _ => catF_le4 H hH.2 k j) h

theorem wp_mod (k : Nat) (h : cWP k (cvOf H k) ≠ 0) : hsize H k % 3 = 1 := by
  obtain ⟨j, hj⟩ := testBit_of_ne_zero h
  exact wpBit_size k _ (fun j _ => catF_le4 H hH.2 k j) j hj

theorem wm_mod (k : Nat) (h : cWM k (cvOf H k) ≠ 0) : hsize H k % 3 = 2 := by
  obtain ⟨j, hj⟩ := testBit_of_ne_zero h
  exact wmBit_size k _ (fun j _ => catF_le4 H hH.2 k j) j hj

end sizes

/-- the standard waits of a hand, as a predicate on tile indices -/
def StdW (H : Counts) (t : Nat) : Prop :=
  t < 34 ∧ fld (cvOf H (t / 9)) (t % 9) < 4 ∧
    ((cP (t / 9) (cvOf H (t / 9) + 16 ^ (t % 9)) = true ∧ ∀ k < 4, k ≠ t / 9 → cM k (cvOf H k) = true) ∨
     (cM (t / 9) (cvOf H (t / 9) + 16 ^ (t % 9)) = true ∧ ∃ y < 4, y ≠ t / 9 ∧ cP y (cvOf H y) = true ∧
        ∀ k < 4, k ≠ t / 9 → k ≠ y → cM k (cvOf H k) = true))

theorem stdW_iff (H : Counts) (t : Nat) : (wStd (cvOf H)).testBit t = true ↔ StdW H t := by
  by_cases ht : t < 34
  · rw [testBit_wStd _ _ ht]; unfold StdW; simp [ht]
  · constructor
    · intro h; exfalso
      -- bits of `wStd` lie below 34
      have : (wStd (cvOf H)).testBit t = false := by
        rw [wStd_eq]
        unfold wStdP
        rw [testBit_lor', Bool.or_eq_false_iff]
        constructor
        · cases hb : (orBelow (fun x => cond (allBelow (fun k => Nat.beq k x || cM k (cvOf H k)) 4)
              (Nat.shiftLeft (cWP x (cvOf H x)) (Nat.mul 9 x)) 0) 4).testBit t
          · rfl
          · rw [testBit_orBelow] at hb
            obtain ⟨x, hx, hb⟩ := hb
            cases hc : allBelow (fun k => Nat.beq k x || cM k (cvOf H k)) 4
            · simp [hc] at hb
            · rw [hc, Bool.cond_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq, testBit_cWP] at hb
              have := cat_of_offset x t hx hb.1 hb.2.1
              have := catLen_le x hx _ hb.2.1
              omega
        · cases hb : (orBelow (fun x => orBelow (fun y =>
              cond (!(Nat.beq y x) && cP y (cvOf H y) && allBelow (fun k => Nat.beq k x || Nat.beq k y || cM k (cvOf H k)) 4)
                (Nat.shiftLeft (cWM x (cvOf H x)) (Nat.mul 9 x)) 0) 4) 4).testBit t
          · rfl
          · rw [testBit_orBelow] at hb
            obtain ⟨x, hx, hb⟩ := hb
            rw [testBit_orBelow] at hb
            obtain ⟨y, hy, hb⟩ := hb
            cases hc : (!(Nat.beq y x) && cP y (cvOf H y) && allBelow (fun k => Nat.beq k x || Nat.beq k y || cM k (cvOf H k)) 4)
            · simp [hc] at hb
            · rw [hc, Bool.cond_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq, testBit_cWM] at hb
              have := cat_of_offset x t hx hb.1 hb.2.1
              have := catLen_le x hx _ hb.2.1
              omega
      rw [this] at h; exact Bool.noConfusion h
    · intro h; exact absurd h.1 ht

/-- in pattern (a) the standard waits are the bits of the single category mask -/
theorem stdW_patA (H : Counts) (hH : IsHand H) (x : Nat) (hp : PatA H x) (t : Nat) :
    StdW H t ↔ (Nat.shiftLeft (cWP x (cvOf H x)) (Nat.mul 9 x)).testBit t = true := by
  obtain ⟨hx, hM, hW⟩ := hp
  have sx := wp_mod H hH x hW
  rw [testBit_shift9, Bool.and_eq_true, decide_eq_true_eq]
  constructor
  · rintro ⟨ht, h4, (⟨hP, hM'⟩ | ⟨hM2, y, hy, hyx, hPy, hrest⟩)⟩
    · by_cases hxt : t / 9 = x
      · subst hxt
        refine ⟨by omega, ?_⟩
        rw [show t - 9 * (t / 9) = t % 9 by omega, testBit_cWP]
        exact ⟨by unfold catLen; split <;> omega, h4, hP⟩
      · exfalso
        have := cM_mod H hH x (hM' x hx (fun e => hxt e.symm))
        omega
    · exfalso
      by_cases hyx' : y = x
      · subst hyx'; have := cP_mod H hH y hPy; omega
      · by_cases hxt : t / 9 = x
        · -- `x` would hold `M` after adding a tile: size ≡ 2, contradiction
          subst hxt
          have hf : ∀ j < catLen (t / 9), catF (extF H) (t / 9) j ≤ 4 := fun j _ => catF_le4 H hH.2 _ j
          have hb : (cWM (t / 9) (cvOf H (t / 9))).testBit (t % 9) = true := by
            rw [testBit_cWM]; exact ⟨by unfold catLen; split <;> omega, h4, hM2⟩
          have := wmBit_size _ _ hf _ hb
          unfold hsize at sx
          omega
        · have := cM_mod H hH x (hrest x hx (fun e => hxt e.symm) (fun e => hyx' e.symm))
          omega
  · rintro ⟨h9, hb⟩
    rw [testBit_cWP] at hb
    obtain ⟨hj, h4, hP⟩ := hb
    have ht : t / 9 = x := cat_of_offset x t hx h9 hj
    subst ht
    rw [show t - 9 * (t / 9) = t % 9 by omega] at h4 hP
    refine ⟨by unfold catLen at hj; split at hj <;> omega, h4, Or.inl ⟨hP, hM⟩⟩

/-- in pattern (b) the standard waits are the bits of the two masks `WM x` and `WM y` -/
theorem stdW_patB (H : Counts) (hH : IsHand H) (x y : Nat) (hp : PatB H x y) (t : Nat) :
    StdW H t ↔ (Nat.lor (cond (cP y (cvOf H y)) (Nat.shiftLeft (cWM x (cvOf H x)) (Nat.mul 9 x)) 0)
                        (cond (cP x (cvOf H x)) (Nat.shiftLeft (cWM y (cvOf H y)) (Nat.mul 9 y)) 0)).testBit t = true := by
  obtain ⟨hx, hy, hxy, hPy, hM, hW⟩ := hp
  have sx := wm_mod H hH x hW
  have sy := cP_mod H hH y hPy
  rw [hPy, Bool.cond_true, testBit_lor', Bool.or_eq_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq]
  have hf : ∀ k, ∀ j < catLen k, catF (extF H) k j ≤ 4 := fun k j _ => catF_le4 H hH.2 k j
  constructor
  · rintro ⟨ht, h4, (⟨hP, hM'⟩ | ⟨hM2, z, hz, hzt, hPz, hrest⟩)⟩
    · exfalso
      -- adding a tile to category t/9 gives pair+melds: t/9 had size ≡ 1, but x or y ≠ t/9 has size ≡ 2
      have hb : (cWP (t / 9) (cvOf H (t / 9))).testBit (t % 9) = true := by
        rw [testBit_cWP]; exact ⟨by unfold catLen; split <;> omega, h4, hP⟩
      have st := wpBit_size _ _ (hf _) _ hb
      by_cases hxt : t / 9 = x
      · have := cM_mod H hH y (hM' y hy (by omega)); omega
      · have := cM_mod H hH x (hM' x hx (fun e => hxt e.symm)); omega
    · have hbm : (cWM (t / 9) (cvOf H (t / 9))).testBit (t % 9) = true := by
        rw [testBit_cWM]; exact ⟨by unfold catLen; split <;> omega, h4, hM2⟩
      have st := wmBit_size _ _ (hf _) _ hbm
      -- the categories other than t/9 and z are melds, so {t/9, z} = {x, y}
      have hz2 := cP_mod H hH z hPz
      by_cases hxt : t / 9 = x
      · subst hxt
        left
        refine ⟨by omega, ?_⟩
        rw [show t - 9 * (t / 9) = t % 9 by omega, testBit_cWM]
        exact ⟨by unfold catLen; split <;> omega, h4, hM2⟩
      · by_cases hyt : t / 9 = y
        · subst hyt
          right
          -- z must be x
          have hzx : z = x := by
            exact Decidable.byContradiction fun hzx => by
              have := cM_mod H hH x (hrest x hx (fun e => hxt e.symm) (fun e => hzx e.symm))
              omega
          subst hzx
          rw [hPz, Bool.cond_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq]
          refine ⟨by omega, ?_⟩
          rw [show t - 9 * (t / 9) = t % 9 by omega, testBit_cWM]
          exact ⟨by unfold catLen; split <;> omega, h4, hM2⟩
        · exfalso
          have h1 := cM_mod H hH (t / 9) (hM (t / 9) (by omega) hxt hyt)
          unfold hsize at h1
          omega
  · rintro (⟨h9, hb⟩ | hb)
    · rw [testBit_cWM] at hb
      obtain ⟨hj, h4, hm⟩ := hb
      have ht : t / 9 = x := cat_of_offset x t hx h9 hj
      subst ht
      rw [show t - 9 * (t / 9) = t % 9 by omega] at h4 hm
      exact ⟨by unfold catLen at hj; split at hj <;> omega, h4, Or.inr ⟨hm, y, hy, fun e => hxy e.symm, hPy,
        fun k hk h1 h2 => hM k hk h1 h2⟩⟩
    · cases hPx : cP x (cvOf H x)
      · rw [hPx, Bool.cond_false] at hb; simp at hb
      · rw [hPx, Bool.cond_true, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq, testBit_cWM] at hb
        obtain ⟨h9, hj, h4, hm⟩ := hb
        have ht : t / 9 = y := cat_of_offset y t hy h9 hj
        subst ht
        rw [show t - 9 * (t / 9) = t % 9 by omega] at h4 hm
        exact ⟨by unfold catLen at hj; split at hj <;> omega, h4, Or.inr ⟨hm, x, hx, hxy, hPx,
          fun k hk h1 h2 => hM k hk h2 h1⟩⟩

/-- a standard wait forces pattern (a) or (b) -/
theorem pattern_of_stdW (H : Counts) (_hH : IsHand H) (t : Nat) (h : StdW H t) :
    (∃ x, PatA H x) ∨ ∃ x y, PatB H x y := by
  obtain ⟨ht, h4, (⟨hP, hM⟩ | ⟨hM2, y, hy, hyx, hPy, hrest⟩)⟩ := h
  · left
    refine ⟨t / 9, by omega, hM, ne_zero_of_testBit (j := t % 9) ?_⟩
    rw [testBit_cWP]; exact ⟨by unfold catLen; split <;> omega, h4, hP⟩
  · right
    refine ⟨t / 9, y, by omega, hy, fun e => hyx e.symm, hPy, hrest, ne_zero_of_testBit (j := t % 9) ?_⟩
    rw [testBit_cWM]; exact ⟨by unfold catLen; split <;> omega, h4, hM2⟩

end Tenpai
