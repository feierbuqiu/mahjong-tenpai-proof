import Tenpai.Enum
import Tenpai.CheckSound2

/-! # What the split checks of `Enum.lean` mean -/

namespace Tenpai

/-! ## `allVecs` -/

theorem allVecs_mul_eq (acc mul d x : Nat) :
    acc + mul * Nat.add d (Nat.mul 16 x) = Nat.add acc (Nat.mul d mul) + Nat.mul 16 mul * x := by
  show acc + mul * (d + 16 * x) = acc + d * mul + 16 * mul * x
  rw [Nat.mul_add, Nat.mul_comm mul d, Nat.mul_assoc 16 mul x, Nat.mul_left_comm mul 16 x, Nat.add_assoc]

theorem sumF_le4 (f : Nat → Nat) : ∀ n, (∀ j < n, f j ≤ 4) → sumF f n ≤ 4 * n
  | 0, _ => Nat.zero_le _
  | n + 1, h => by
    have := sumF_le4 f n (fun j hj => h j (by omega))
    have := h n (by omega)
    show sumF f n + f n ≤ 4 * (n + 1)
    omega

theorem vecs_sum_le {npos rem x : Nat} (hx : x ∈ vecs npos rem) : rem ≤ 4 * npos := by
  obtain ⟨f, hf, hs, -⟩ := (mem_vecs npos rem x).mp hx
  rw [← hs]
  exact sumF_le4 f npos hf

theorem allVecs_iff (f : Nat → Bool) : ∀ npos rem acc mul,
    allVecs f npos rem acc mul = true ↔ ∀ x ∈ vecs npos rem, f (acc + mul * x) = true
  | 0, rem, acc, mul => by
    show cond (Nat.beq rem 0) (force acc f) true = true ↔ ∀ x ∈ cond (Nat.beq rem 0) [0] [], _
    cases Nat.beq rem 0
    · simp
    · simp [force_eq]
  | npos + 1, rem, acc, mul => by
    show allBelow (fun d => !(Nat.ble d rem) || !(Nat.ble (Nat.sub rem d) (Nat.mul 4 npos)) ||
        allVecs f npos (Nat.sub rem d) (Nat.add acc (Nat.mul d mul)) (Nat.mul 16 mul)) 5 = true ↔
      ∀ x ∈ List.flatMap (fun d => cond (Nat.ble d rem)
        ((vecs npos (Nat.sub rem d)).map (fun x => Nat.add d (Nat.mul 16 x))) []) [0, 1, 2, 3, 4],
        f (acc + mul * x) = true
    rw [allBelow_iff]
    constructor
    · intro h x hx
      rw [List.mem_flatMap] at hx
      obtain ⟨d, hd, hx⟩ := hx
      have hd5 : d < 5 := by simp at hd; omega
      have hdd := h d hd5
      cases hb : Nat.ble d rem
      · rw [hb] at hx; simp at hx
      · rw [hb, Bool.cond_true, List.mem_map] at hx
        obtain ⟨x', hx', rfl⟩ := hx
        have hle : Nat.ble (Nat.sub rem d) (Nat.mul 4 npos) = true :=
          Nat.ble_eq.mpr (vecs_sum_le hx')
        rw [hb, hle] at hdd
        simp only [Bool.not_true, Bool.false_or] at hdd
        rw [allVecs_mul_eq]
        exact (allVecs_iff f npos _ _ _).mp hdd x' hx'
    · intro h d hd
      cases hb : Nat.ble d rem
      · rfl
      · cases hle : Nat.ble (Nat.sub rem d) (Nat.mul 4 npos)
        · simp
        · simp only [Bool.not_true, Bool.false_or]
          rw [allVecs_iff f npos]
          intro x' hx'
          have hmem : Nat.add d (Nat.mul 16 x') ∈ List.flatMap (fun d => cond (Nat.ble d rem)
              ((vecs npos (Nat.sub rem d)).map (fun x => Nat.add d (Nat.mul 16 x))) []) [0, 1, 2, 3, 4] := by
            rw [List.mem_flatMap]
            refine ⟨d, by simp; omega, ?_⟩
            rw [hb, Bool.cond_true]
            exact List.mem_map.mpr ⟨x', hx', rfl⟩
          have := h _ hmem
          rw [allVecs_mul_eq] at this
          exact this

/-- one step of the prefix tree: every value `d` of the lowest free field that can still reach
    the sum `rem` -/
theorem allVecs_node (f : Nat → Bool) (npos rem acc mul : Nat)
    (h : ∀ d, d < 5 → d ≤ rem → rem - d ≤ 4 * npos →
      allVecs f npos (rem - d) (acc + d * mul) (16 * mul) = true) :
    allVecs f (npos + 1) rem acc mul = true := by
  show allBelow (fun d => !(Nat.ble d rem) || !(Nat.ble (Nat.sub rem d) (Nat.mul 4 npos)) ||
    allVecs f npos (Nat.sub rem d) (Nat.add acc (Nat.mul d mul)) (Nat.mul 16 mul)) 5 = true
  rw [allBelow_iff]
  intro d hd
  cases hb : Nat.ble d rem
  · rfl
  · cases hle : Nat.ble (Nat.sub rem d) (Nat.mul 4 npos)
    · simp
    · simp only [Bool.not_true, Bool.false_or]
      exact h d hd (Nat.le_of_ble_eq_true hb) (Nat.le_of_ble_eq_true hle)

theorem allVecs_root (f : Nat → Bool) (npos rem : Nat) (h : allVecs f npos rem 0 1 = true) :
    ∀ x ∈ vecs npos rem, f x = true := by
  intro x hx
  have := (allVecs_iff f npos rem 0 1).mp h x hx
  simpa using this

/-! ## the list functions -/

theorem mapL_eq {α β : Type} (f : α → β) : ∀ l : List α, mapL f l = l.map f
  | [] => rfl
  | a :: l => by
    show f a :: mapL f l = _
    rw [mapL_eq f l]; rfl

theorem appendL_eq {α : Type} : ∀ l₁ l₂ : List α, appendL l₁ l₂ = l₁ ++ l₂
  | [], _ => rfl
  | a :: l, l₂ => by
    show a :: appendL l l₂ = _
    rw [appendL_eq l l₂]; rfl

theorem filterL_eq {α : Type} (p : α → Bool) : ∀ l : List α, filterL p l = l.filter p
  | [] => rfl
  | a :: l => by
    show cond (p a) (a :: filterL p l) (filterL p l) = _
    rw [filterL_eq p l, List.filter_cons]
    cases p a <;> rfl

theorem flatMapL_eq {α β : Type} (f : α → List β) : ∀ l : List α, flatMapL f l = l.flatMap f
  | [] => rfl
  | a :: l => by
    show appendL (f a) (flatMapL f l) = _
    rw [appendL_eq, flatMapL_eq f l, List.flatMap_cons]

theorem vecsL_eq : ∀ npos rem, vecsL npos rem = vecs npos rem
  | 0, _ => rfl
  | npos + 1, rem => by
    show flatMapL (fun d => cond (Nat.ble d rem) (mapL (fun x => Nat.add d (Nat.mul 16 x))
        (vecsL npos (Nat.sub rem d))) []) [0, 1, 2, 3, 4] =
      List.flatMap (fun d => cond (Nat.ble d rem)
        ((vecs npos (Nat.sub rem d)).map (fun x => Nat.add d (Nat.mul 16 x))) []) [0, 1, 2, 3, 4]
    rw [flatMapL_eq]
    congr 1
    funext d
    rw [mapL_eq, vecsL_eq npos]

theorem innerL_eq (y ny : Nat) : innerL y ny = ((vecs (catLen y) ny).map (infOf y)).filter relevant := by
  unfold innerL
  rw [filterL_eq, mapL_eq, vecsL_eq]

/-! ## T1 and T2 -/

theorem t1_of_allVecs (tree : PTree (List Nat)) (k n : Nat)
    (h : allVecs (t1unit tree k n) (catLen k) n 0 1 = true) :
    ∀ u ∈ vecs (catLen k) n, t1unit tree k n u = true :=
  allVecs_root _ _ _ h

theorem t2_of_allVecs (tree : PTree (List Nat)) (x y nx ny : Nat)
    (h : allVecs (t2outer tree x y nx ny (innerL y ny)) (catLen x) nx 0 1 = true) :
    ∀ u ∈ vecs (catLen x) nx, ∀ v ∈ vecs (catLen y) ny, T2unit tree x y nx ny u v := by
  intro u hu v hv
  have hu' := allVecs_root _ _ _ h u hu
  unfold t2outer at hu'
  rw [innerL_eq] at hu'
  apply t2pair_unit
  rw [Bool.or_eq_true] at hu'
  rcases hu' with hr | hall
  · exact Or.inl (by simpa using hr)
  · by_cases hry : relevant (infOf y v) = true
    · have hmem : infOf y v ∈ ((vecs (catLen y) ny).map (infOf y)).filter relevant :=
        List.mem_filter.mpr ⟨List.mem_map.mpr ⟨v, hv, rfl⟩, hry⟩
      exact Or.inr (Or.inr ((allL_iff _ _).mp hall _ hmem))
    · exact Or.inr (Or.inl (by simpa using hry))

theorem t2rev_of_allVecs (tree : PTree (List Nat)) (x y nx ny : Nat)
    (h : allVecs (t2outerRev tree x y nx ny (innerL x nx)) (catLen y) ny 0 1 = true) :
    ∀ u ∈ vecs (catLen x) nx, ∀ v ∈ vecs (catLen y) ny, T2unit tree x y nx ny u v := by
  intro u hu v hv
  have hv' := allVecs_root _ _ _ h v hv
  unfold t2outerRev at hv'
  rw [innerL_eq] at hv'
  apply t2pair_unit
  rw [Bool.or_eq_true] at hv'
  rcases hv' with hr | hall
  · exact Or.inr (Or.inl (by simpa using hr))
  · by_cases hrx : relevant (infOf x u) = true
    · have hmem : infOf x u ∈ ((vecs (catLen x) nx).map (infOf x)).filter relevant :=
        List.mem_filter.mpr ⟨List.mem_map.mpr ⟨u, hu, rfl⟩, hrx⟩
      exact Or.inr (Or.inr ((allL_iff _ _).mp hall _ hmem))
    · exact Or.inl (by simpa using hrx)

/-! ## T4 -/

theorem bool_merge (S A B C P : Bool) (h1 : (!S || !A || B || P) = true) (h2 : (!S || !B || C || P) = true) :
    (!S || !A || C || P) = true := by
  revert h1 h2
  cases S <;> cases A <;> cases B <;> cases C <;> cases P <;> decide

theorem forShapesR_merge (p : (Nat → Nat) → Bool) (a b c : Nat)
    (h1 : forShapesR p a b = true) (h2 : forShapesR p b c = true) : forShapesR p a c = true := by
  unfold forShapesR at *
  rw [allBelow_iff] at h1 h2 ⊢
  intro n0 hn0
  have h1 := h1 n0 hn0
  have h2 := h2 n0 hn0
  rw [allBelow_iff] at h1 h2 ⊢
  intro n1 hn1
  have h1 := h1 n1 hn1
  have h2 := h2 n1 hn1
  rw [allBelow_iff] at h1 h2 ⊢
  intro n2 hn2
  exact bool_merge _ _ _ _ _ (h1 n2 hn2) (h2 n2 hn2)

theorem forShapes_of_R (p : (Nat → Nat) → Bool) (h : forShapesR p 0 2744 = true) : forShapes p = true := by
  unfold forShapesR at h
  unfold forShapes
  rw [allBelow_iff] at *
  intro n0 hn0
  have h := h n0 hn0
  rw [allBelow_iff] at *
  intro n1 hn1
  have h := h n1 hn1
  rw [allBelow_iff] at *
  intro n2 hn2
  have h := h n2 hn2
  have e1 : Nat.ble 0 (Nat.add (Nat.mul 196 n0) (Nat.add (Nat.mul 14 n1) n2)) = true := Nat.ble_eq.mpr (Nat.zero_le _)
  have e2 : Nat.ble 2744 (Nat.add (Nat.mul 196 n0) (Nat.add (Nat.mul 14 n1) n2)) = false := by
    cases hb : Nat.ble 2744 (Nat.add (Nat.mul 196 n0) (Nat.add (Nat.mul 14 n1) n2))
    · rfl
    · have := Nat.le_of_ble_eq_true hb
      exfalso
      show False
      have : 2744 ≤ 196 * n0 + (14 * n1 + n2) := this
      omega
  rw [e1, e2] at h
  simpa using h

theorem t4okA_eq (tree : PTree (List Nat)) (x : Nat) : t4okA tree x = forShapes (pA tree x) := rfl

theorem t4okB_eq (tree : PTree (List Nat)) (x y : Nat) : t4okB tree x y = forShapes (pB tree x y) := rfl

end Tenpai
