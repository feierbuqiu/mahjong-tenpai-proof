import Tenpai.Basic

/-!
# Packed count vectors

`pkF f n = ∑_{j<n} f j · 16^j`.  When every `f j < 16`, field `j` of `pkF f n` is `f j`.
-/

namespace Tenpai

/-- pack the first `n` values of `f`, 4 bits each -/
def pkF (f : Nat → Nat) : Nat → Nat
  | 0 => 0
  | n + 1 => pkF f n + f n * 16 ^ n

/-- `∑_{j<n} f j` -/
def sumF (f : Nat → Nat) : Nat → Nat
  | 0 => 0
  | n + 1 => sumF f n + f n

theorem pkF_zero (f : Nat → Nat) : pkF f 0 = 0 := rfl
theorem pkF_succ (f : Nat → Nat) (n : Nat) : pkF f (n + 1) = pkF f n + f n * 16 ^ n := rfl

theorem pkF_split (f : Nat → Nat) (a : Nat) :
    ∀ b, pkF f (a + b) = pkF f a + 16 ^ a * pkF (fun i => f (a + i)) b
  | 0 => by simp [pkF]
  | b + 1 => by
    rw [← Nat.add_assoc, pkF_succ, pkF_split f a b, pkF_succ, Nat.pow_add]
    simp only [Nat.mul_add]
    rw [Nat.add_assoc]
    congr 2
    rw [Nat.mul_left_comm]

theorem pkF_congr {f g : Nat → Nat} : ∀ {n}, (∀ j < n, f j = g j) → pkF f n = pkF g n
  | 0, _ => rfl
  | n + 1, h => by
    rw [pkF_succ, pkF_succ, pkF_congr (fun j hj => h j (by omega)), h n (by omega)]

theorem pkF_cons (f : Nat → Nat) (n : Nat) : pkF f (n + 1) = f 0 + 16 * pkF (fun j => f (j + 1)) n := by
  have h := pkF_split f 1 n
  rw [Nat.add_comm 1 n] at h
  rw [h]
  simp only [pkF, Nat.zero_add, Nat.pow_zero, Nat.mul_one, Nat.pow_one]
  congr 2
  exact pkF_congr (fun i _ => by rw [Nat.add_comm])

theorem pkF_add (f g : Nat → Nat) : ∀ n, pkF (fun j => f j + g j) n = pkF f n + pkF g n
  | 0 => rfl
  | n + 1 => by
    rw [pkF_succ, pkF_succ, pkF_succ, pkF_add f g n, Nat.add_mul]
    omega

theorem pkF_mul_const (c : Nat) (f : Nat → Nat) : ∀ n, pkF (fun j => c * f j) n = c * pkF f n
  | 0 => rfl
  | n + 1 => by
    rw [pkF_succ, pkF_succ, pkF_mul_const c f n, Nat.mul_add, Nat.mul_assoc]

theorem pkF_lt (f : Nat → Nat) : ∀ n, (∀ j < n, f j < 16) → pkF f n < 16 ^ n
  | 0, _ => by simp [pkF]
  | n + 1, h => by
    rw [pkF_succ, Nat.pow_succ]
    have h1 := pkF_lt f n (fun j hj => h j (by omega))
    have h2 : f n ≤ 15 := by have := h n (by omega); omega
    have h3 : f n * 16 ^ n ≤ 15 * 16 ^ n := Nat.mul_le_mul_right _ h2
    omega

theorem pkF_single (j : Nat) : ∀ n, j < n → pkF (fun i => if i = j then 1 else 0) n = 16 ^ j
  | 0, h => absurd h (by omega)
  | n + 1, h => by
    rw [pkF_succ]
    by_cases hj : j = n
    · subst hj
      rw [pkF_congr (g := fun _ => 0) (fun i hi => by simp; omega)]
      have : ∀ m, pkF (fun _ => 0) m = 0 := by
        intro m; induction m with
        | zero => rfl
        | succ m ih => rw [pkF_succ, ih]; simp
      simp [this]
    · rw [pkF_single j n (by omega)]
      simp [show n ≠ j from fun e => hj e.symm]

/-- generic: field `j` is `u / 16^j % 16` -/
theorem fld_eq (u j : Nat) : fld u j = u / 16 ^ j % 16 := by
  unfold fld
  have h1 : Nat.shiftRight u (Nat.mul 4 j) = u / 16 ^ j := by
    show u >>> (4 * j) = u / 16 ^ j
    rw [Nat.shiftRight_eq_div_pow, Nat.pow_mul]
  have h2 : ∀ x : Nat, Nat.land x 15 = x % 16 := fun x => by
    have := Nat.and_two_pow_sub_one_eq_mod x 4
    simpa using this
  rw [h1, h2]

theorem fld_pkF (f : Nat → Nat) (n : Nat) (hf : ∀ i < n, f i < 16) (j : Nat) :
    fld (pkF f n) j = if j < n then f j else 0 := by
  rw [fld_eq]
  split
  · next hj =>
    have hs := pkF_split f j (n - j)
    rw [show j + (n - j) = n by omega] at hs
    obtain ⟨m, hm⟩ : ∃ m, n - j = m + 1 := ⟨n - j - 1, by omega⟩
    rw [hm, pkF_cons] at hs
    rw [hs]
    have hlt := pkF_lt f j (fun i hi => hf i (by omega))
    have : (pkF f j + 16 ^ j * (f (j + 0) + 16 * pkF (fun j_1 => f (j + (j_1 + 1))) m)) / 16 ^ j
        = f (j + 0) + 16 * pkF (fun j_1 => f (j + (j_1 + 1))) m := by
      rw [Nat.mul_comm (16 ^ j), Nat.add_mul_div_right _ _ (Nat.pow_pos (by omega)),
        Nat.div_eq_of_lt hlt, Nat.zero_add]
    rw [this]
    simp only [Nat.add_zero]
    rw [Nat.add_mul_mod_self_left]
    exact Nat.mod_eq_of_lt (hf j hj)
  · next hj =>
    have hlt := pkF_lt f n hf
    have : pkF f n / 16 ^ j = 0 := Nat.div_eq_of_lt (Nat.lt_of_lt_of_le hlt
      (Nat.pow_le_pow_right (by omega) (by omega)))
    rw [this]

theorem pkF_add_single (f : Nat → Nat) (n : Nat) (t : Nat) (ht : t < n) :
    pkF f n + 16 ^ t = pkF (fun i => if i = t then f i + 1 else f i) n := by
  rw [← pkF_single t n ht, ← pkF_add]
  apply pkF_congr
  intro j _
  split <;> simp_all

theorem pkF_sub_pair (f : Nat → Nat) (n : Nat) (p : Nat) (hp : p < n) (hfp : 2 ≤ f p) :
    pkF f n - 2 * 16 ^ p = pkF (fun i => if i = p then f i - 2 else f i) n := by
  have h : pkF (fun i => if i = p then f i - 2 else f i) n + 2 * 16 ^ p = pkF f n := by
    rw [← pkF_single p n hp, ← pkF_mul_const, ← pkF_add]
    apply pkF_congr
    intro j _
    split <;> simp_all <;> omega
  omega

/-- bit `4q + r` of `u` is bit `r` of field `q` -/
theorem testBit_fld (u q r : Nat) (hr : r < 4) : u.testBit (4 * q + r) = (fld u q).testBit r := by
  rw [fld_eq, show (16 : Nat) = 2 ^ 4 from rfl, ← Nat.pow_mul, Nat.testBit_mod_two_pow,
    Nat.testBit_div_two_pow]
  simp [hr, Nat.add_comm]

/-- two numbers are equal iff all their fields are -/
theorem eq_of_fld_eq {x y : Nat} (h : ∀ q, fld x q = fld y q) : x = y := by
  apply Nat.eq_of_testBit_eq
  intro i
  have : i = 4 * (i / 4) + i % 4 := by omega
  rw [this, testBit_fld _ _ _ (Nat.mod_lt _ (by omega)), testBit_fld _ _ _ (Nat.mod_lt _ (by omega)), h]

theorem fld_land (x y q : Nat) : fld (Nat.land x y) q = Nat.land (fld x q) (fld y q) := by
  have hb : ∀ v : Nat, fld v q < 16 := fun v => by rw [fld_eq]; exact Nat.mod_lt _ (by omega)
  apply Nat.eq_of_testBit_eq
  intro r
  by_cases hr : r < 4
  · show (fld (x &&& y) q).testBit r = (fld x q &&& fld y q).testBit r
    rw [← testBit_fld _ _ _ hr, Nat.testBit_and, Nat.testBit_and, testBit_fld _ _ _ hr, testBit_fld _ _ _ hr]
  · have h1 : ∀ v : Nat, v < 16 → v.testBit r = false := fun v hv => by
      apply Nat.testBit_lt_two_pow
      exact Nat.lt_of_lt_of_le hv (by
        have : (16:Nat) = 2 ^ 4 := rfl
        rw [this]; exact Nat.pow_le_pow_right (by omega) (by omega))
    rw [h1 _ (hb _)]
    show false = (fld x q &&& fld y q).testBit r
    rw [Nat.testBit_and, h1 _ (hb _)]
    simp

/-- the guard constant: field 8 in each of the 34 positions -/
theorem guard_eq : guard = pkF (fun _ => 8) 34 := by decide

theorem fld_guard (q : Nat) : fld guard q = if q < 34 then 8 else 0 := by
  rw [guard_eq, fld_pkF _ _ (fun _ _ => by omega)]

theorem land8_iff : ∀ x, x < 16 → (Nat.land x 8 = 8 ↔ 8 ≤ x) := by decide

/-- correctness of the SWAR sub-multiset test -/
theorem fits_iff (fc fh : Nat → Nat) (hc : ∀ j < 34, fc j ≤ 4) (hh : ∀ j < 34, fh j ≤ 4) :
    fits (pkF fc 34) (pkF fh 34) = true ↔ ∀ j < 34, fc j ≤ fh j := by
  let d : Nat → Nat := fun j => fh j + 8 - fc j
  have hd : Nat.sub (Nat.add (pkF fh 34) guard) (pkF fc 34) = pkF d 34 := by
    show pkF fh 34 + guard - pkF fc 34 = pkF d 34
    have : pkF d 34 + pkF fc 34 = pkF fh 34 + guard := by
      rw [← pkF_add, guard_eq, ← pkF_add]
      apply pkF_congr
      intro j hj
      have := hc j hj
      show fh j + 8 - fc j + fc j = fh j + 8
      omega
    omega
  have hdb : ∀ j < 34, d j < 16 := fun j hj => by
    have := hc j hj; have := hh j hj; show fh j + 8 - fc j < 16; omega
  have key : ∀ j < 34, (8 ≤ d j ↔ fc j ≤ fh j) := fun j hj => by
    have := hc j hj; show 8 ≤ fh j + 8 - fc j ↔ fc j ≤ fh j; omega
  unfold fits
  rw [hd, Nat.beq_eq]
  constructor
  · intro he j hj
    have := congrArg (fun x => fld x j) he
    rw [fld_land, fld_guard, fld_pkF _ _ hdb] at this
    simp only [hj, ite_true] at this
    exact (key j hj).mp ((land8_iff _ (hdb j hj)).mp this)
  · intro h
    apply eq_of_fld_eq
    intro q
    rw [fld_land, fld_guard, fld_pkF _ _ hdb]
    by_cases hq : q < 34
    · simp only [hq, ite_true]
      exact (land8_iff _ (hdb q hq)).mpr ((key q hq).mpr (h q hq))
    · simp [hq]

end Tenpai
