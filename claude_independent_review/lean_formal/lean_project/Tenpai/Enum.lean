import Tenpai.Checks

/-!
# Kernel-friendly forms of the large checks

The kernel caches every term it evaluates while checking one declaration, so the memory a
check needs grows with its work.  The large checks are therefore split into many small
declarations, and this file provides the forms they are stated in:

* `allVecs f npos rem acc mul`: `f` holds on `acc + mul·x` for every packed vector `x`
  (`npos` fields `≤ 4`, field sum `rem`).  No list is built, and fixing the lowest fields
  of `x` (a *prefix*) gives the sub-enumerations used as chunks of T1 and T2.
* `mapL`, `filterL`, `flatMapL`, `vecsL`: `List.rec` versions of the core list functions
  (the kernel reduces those through their structural-recursion encoding, which is costly);
  they build the small inner list of T2 once per declaration.
* `forShapesR p lo hi`: `forShapes` restricted to the shapes with index in `[lo, hi)`,
  used to split T4 by shapes.

`EnumSound.lean` proves that these checks imply the fields of `Checked`.
-/

namespace Tenpai

/-- `f (acc + mul·x)` for all packed vectors `x` with `npos` fields `≤ 4` and field sum `rem`
    (branches that cannot reach the sum `rem` are cut) -/
noncomputable def allVecs (f : Nat → Bool) : Nat → Nat → Nat → Nat → Bool :=
  Nat.rec (motive := fun _ => Nat → Nat → Nat → Bool)
    (fun rem acc _ => cond (Nat.beq rem 0) (force acc f) true)
    (fun m ih rem acc mul => allBelow (fun d => !(Nat.ble d rem) || !(Nat.ble (Nat.sub rem d) (Nat.mul 4 m)) ||
      ih (Nat.sub rem d) (Nat.add acc (Nat.mul d mul)) (Nat.mul 16 mul)) 5)

/-! ## lists without structural recursion -/

noncomputable def mapL {α β : Type} (f : α → β) (l : List α) : List β :=
  List.rec (motive := fun _ => List β) [] (fun a _ ih => f a :: ih) l

noncomputable def appendL {α : Type} (l₁ l₂ : List α) : List α :=
  List.rec (motive := fun _ => List α) l₂ (fun a _ ih => a :: ih) l₁

noncomputable def filterL {α : Type} (p : α → Bool) (l : List α) : List α :=
  List.rec (motive := fun _ => List α) [] (fun a _ ih => cond (p a) (a :: ih) ih) l

noncomputable def flatMapL {α β : Type} (f : α → List β) (l : List α) : List β :=
  List.rec (motive := fun _ => List β) [] (fun a _ ih => appendL (f a) ih) l

/-- the same list as `vecs` -/
noncomputable def vecsL : Nat → Nat → List Nat :=
  Nat.rec (motive := fun _ => Nat → List Nat)
    (fun rem => cond (Nat.beq rem 0) [0] [])
    (fun _ ih rem =>
      flatMapL (fun d => cond (Nat.ble d rem) (mapL (fun x => Nat.add d (Nat.mul 16 x)) (ih (Nat.sub rem d))) [])
        [0, 1, 2, 3, 4])

/-! ## T1 and T2 per outer vector -/

/-- the relevant category vectors of category `y` with `ny` tiles, with their information -/
noncomputable def innerL (y ny : Nat) : List Inf := filterL relevant (mapL (infOf y) (vecsL (catLen y) ny))

/-- T2 for one outer vector `u` of category `x` against all inner vectors of category `y` -/
noncomputable def t2outer (tree : PTree (List Nat)) (x y nx ny : Nat) (inner : List Inf) (u : Nat) : Bool :=
  !(relevant (infOf x u)) || allL (t2pair tree (catsExcept2 x y) (Nat.add nx ny) (infOf x u)) inner

/-- T2 for one outer vector `v` of category `y` against all inner vectors of category `x` -/
noncomputable def t2outerRev (tree : PTree (List Nat)) (x y nx ny : Nat) (inner : List Inf) (v : Nat) : Bool :=
  !(relevant (infOf y v)) || allL (fun a => t2pair tree (catsExcept2 x y) (Nat.add nx ny) a (infOf y v)) inner

/-! ## T4 by ranges of shapes -/

/-- `forShapes p`, restricted to the shapes with index `lo ≤ 196·n₀ + 14·n₁ + n₂ < hi` -/
noncomputable def forShapesR (p : (Nat → Nat) → Bool) (lo hi : Nat) : Bool :=
  allBelow (fun n0 => allBelow (fun n1 => allBelow (fun n2 =>
    !(Nat.ble (Nat.add n0 (Nat.add n1 n2)) 13) ||
    !(Nat.ble lo (Nat.add (Nat.mul 196 n0) (Nat.add (Nat.mul 14 n1) n2))) ||
    Nat.ble hi (Nat.add (Nat.mul 196 n0) (Nat.add (Nat.mul 14 n1) n2)) ||
    p (sel4 n0 n1 n2 (Nat.sub 13 (Nat.add n0 (Nat.add n1 n2)))))
    14) 14) 14

/-- the per-shape test of `t4okA` -/
noncomputable def pA (tree : PTree (List Nat)) (x : Nat) : (Nat → Nat) → Bool :=
  fun n => !(shape1 x n) || t4shape (fun k => Nat.beq k x) n (t4handA tree x)

/-- the per-shape test of `t4okB` -/
noncomputable def pB (tree : PTree (List Nat)) (x y : Nat) : (Nat → Nat) → Bool :=
  fun n => !(shape2 x y n) || t4shape (fun k => Nat.beq k x || Nat.beq k y) n (t4handB tree x y)

end Tenpai
