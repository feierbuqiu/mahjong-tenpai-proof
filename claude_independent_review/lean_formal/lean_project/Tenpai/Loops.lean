import Tenpai.Packed

/-! # Semantics of the kernel loops (`anyBelow`, `maskBelow`, `anyL`, `allL`, `vecs`, `PTree.find`) -/

namespace Tenpai

theorem anyBelow_iff (f : Nat → Bool) : ∀ n, anyBelow f n = true ↔ ∃ i < n, f i = true
  | 0 => by simp [anyBelow]
  | n + 1 => by
    show (f n || anyBelow f n) = true ↔ _
    rw [Bool.or_eq_true, anyBelow_iff f n]
    constructor
    · rintro (h | ⟨i, hi, h⟩)
      · exact ⟨n, by omega, h⟩
      · exact ⟨i, by omega, h⟩
    · rintro ⟨i, hi, h⟩
      by_cases hin : i = n
      · subst hin; exact Or.inl h
      · exact Or.inr ⟨i, by omega, h⟩

theorem maskBelow_zero (f : Nat → Bool) : maskBelow f 0 = 0 := rfl

theorem testBit_maskBelow (f : Nat → Bool) : ∀ n i, (maskBelow f n).testBit i = (decide (i < n) && f i)
  | 0, i => by rw [maskBelow_zero]; simp
  | n + 1, i => by
    show (cond (f n) (Nat.lor (Nat.shiftLeft 1 n) (maskBelow f n)) (maskBelow f n)).testBit i = _
    have ih := testBit_maskBelow f n i
    cases hfn : f n
    · simp only [Bool.cond_false, ih]
      by_cases hin : i = n
      · subst hin; simp [hfn]
      · have : (i < n + 1) = (i < n) := by apply propext; omega
        simp [this]
    · simp only [Bool.cond_true]
      show (1 <<< n ||| maskBelow f n).testBit i = _
      rw [Nat.testBit_or, ih, Nat.one_shiftLeft, Nat.testBit_two_pow]
      by_cases hin : i = n
      · subst hin; simp [hfn]
      · have : (i < n + 1) = (i < n) := by apply propext; omega
        simp [this, show ¬ n = i from fun e => hin e.symm]

theorem maskBelow_lt (f : Nat → Bool) : ∀ n, maskBelow f n < 2 ^ n
  | 0 => by rw [maskBelow_zero]; simp
  | n + 1 => by
    show cond (f n) (Nat.lor (Nat.shiftLeft 1 n) (maskBelow f n)) (maskBelow f n) < 2 ^ (n + 1)
    have ih := maskBelow_lt f n
    have hp : 2 ^ n < 2 ^ (n + 1) := Nat.pow_lt_pow_right (by omega) (by omega)
    cases f n
    · simp only [Bool.cond_false]; omega
    · simp only [Bool.cond_true]
      show 1 <<< n ||| maskBelow f n < 2 ^ (n + 1)
      apply Nat.or_lt_two_pow
      · rw [Nat.one_shiftLeft]; exact hp
      · omega

theorem anyL_iff {α : Type} (f : α → Bool) : ∀ l : List α, anyL f l = true ↔ ∃ a ∈ l, f a = true
  | [] => by simp [anyL]
  | a :: l => by
    show (f a || anyL f l) = true ↔ _
    rw [Bool.or_eq_true, anyL_iff f l]
    simp

theorem allL_iff {α : Type} (f : α → Bool) : ∀ l : List α, allL f l = true ↔ ∀ a ∈ l, f a = true
  | [] => by simp [allL]
  | a :: l => by
    show (f a && allL f l) = true ↔ _
    rw [Bool.and_eq_true, allL_iff f l]
    simp

/-- membership in `vecs`: packed vectors of `npos` fields `≤ 4` with field sum `rem` -/
theorem mem_vecs : ∀ npos rem u, u ∈ vecs npos rem ↔
    ∃ f : Nat → Nat, (∀ j < npos, f j ≤ 4) ∧ sumF f npos = rem ∧ u = pkF f npos
  | 0, rem, u => by
    show u ∈ cond (Nat.beq rem 0) [0] [] ↔ _
    cases h : Nat.beq rem 0
    · have : rem ≠ 0 := fun e => by subst e; simp at h
      simp only [Bool.cond_false, List.not_mem_nil, false_iff]
      rintro ⟨f, -, hs, -⟩
      exact this (by rw [← hs]; rfl)
    · have : rem = 0 := Nat.eq_of_beq_eq_true h
      subst this
      simp only [Bool.cond_true, List.mem_singleton]
      constructor
      · rintro rfl; exact ⟨fun _ => 0, by simp, rfl, rfl⟩
      · rintro ⟨f, -, -, rfl⟩; rfl
  | npos + 1, rem, u => by
    show u ∈ List.flatMap (fun d => cond (Nat.ble d rem)
      ((vecs npos (Nat.sub rem d)).map (fun x => Nat.add d (Nat.mul 16 x))) []) [0, 1, 2, 3, 4] ↔ _
    rw [List.mem_flatMap]
    constructor
    · rintro ⟨d, hd, hu⟩
      have hd4 : d ≤ 4 := by simp at hd; omega
      cases hb : Nat.ble d rem
      · simp [hb] at hu
      · have hdr : d ≤ rem := Nat.le_of_ble_eq_true hb
        simp only [hb, Bool.cond_true, List.mem_map] at hu
        obtain ⟨x, hx, rfl⟩ := hu
        obtain ⟨g, hg, hgs, rfl⟩ := (mem_vecs npos (rem - d) x).mp hx
        refine ⟨fun j => if j = 0 then d else g (j - 1), ?_, ?_, ?_⟩
        · intro j hj
          by_cases h0 : j = 0
          · simp [h0, hd4]
          · simp only [h0, ite_false]; exact hg _ (by omega)
        · -- sum of the shifted function
          have : ∀ n, sumF (fun j => if j = 0 then d else g (j - 1)) (n + 1) = d + sumF g n := by
            intro n
            induction n with
            | zero => simp [sumF]
            | succ n ih => rw [sumF, ih, sumF]; simp; omega
          rw [this, hgs]; show d + (rem - d) = rem; omega
        · rw [pkF_cons]
          show d + 16 * pkF g npos = _
          simp
    · rintro ⟨f, hf, hs, rfl⟩
      refine ⟨f 0, by have := hf 0 (by omega); simp; omega, ?_⟩
      have hsum : sumF f (npos + 1) = f 0 + sumF (fun j => f (j + 1)) npos := by
        clear hs hf
        induction npos with
        | zero => simp [sumF]
        | succ n ih => rw [sumF, ih, sumF]; omega
      have hle : f 0 ≤ rem := by rw [← hs, hsum]; omega
      have hb : Nat.ble (f 0) rem = true := Nat.ble_eq.mpr hle
      simp only [hb, Bool.cond_true, List.mem_map]
      refine ⟨pkF (fun j => f (j + 1)) npos, ?_, ?_⟩
      · rw [mem_vecs npos]
        exact ⟨fun j => f (j + 1), fun j hj => hf _ (by omega), by rw [← hs, hsum]; show _ = f 0 + _ - f 0; omega, rfl⟩
      · rw [pkF_cons]; rfl

/-- lookup soundness -/
theorem PTree.find_mem {β : Type} (dflt : β) (t : PTree β) (x : Nat) :
    t.find dflt x = dflt ∨ (x, t.find dflt x) ∈ t.toList := by
  induction t with
  | leaf => exact Or.inl rfl
  | node l k v r ihl ihr =>
    show cond (Nat.blt x k) (l.find dflt x) (cond (Nat.beq x k) v (r.find dflt x)) = dflt ∨
      (x, cond (Nat.blt x k) (l.find dflt x) (cond (Nat.beq x k) v (r.find dflt x))) ∈ (l.toList ++ (k, v) :: r.toList)
    cases hlt : Nat.blt x k
    · cases heq : Nat.beq x k
      · simp only [Bool.cond_false]
        rcases ihr with h | h
        · exact Or.inl h
        · exact Or.inr (by simp [h])
      · simp only [Bool.cond_false, Bool.cond_true]
        have : x = k := Nat.eq_of_beq_eq_true heq
        subst this
        exact Or.inr (by simp)
    · simp only [Bool.cond_true]
      rcases ihl with h | h
      · exact Or.inl h
      · exact Or.inr (by simp [h])

end Tenpai
