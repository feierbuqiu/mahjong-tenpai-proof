/-!
# Computational core

Everything here is written for the Lean *kernel*: primitive `Nat` operations
(which the kernel evaluates with GMP), `Nat.rec`/`List.rec` instead of
compiled structural recursion, and `force`, which makes the kernel's
evaluation cache work as a memo table keyed by value.

Count vectors are *packed*: field `j` (bits `4j … 4j+3`) holds the count of
position `j`.  A category (suit or honours) is handled as a local vector of
`len` positions; sequences may start at local positions `j < lim`
(suits: `len = 9`, `lim = 7`; honours: `len = 7`, `lim = 0`).
-/

namespace Tenpai

/-- `force e k = k e`, but the kernel first evaluates `e` to a literal, so `k e` is cached by value -/
def force {α : Sort u} (e : Nat) (k : Nat → α) : α :=
  Nat.casesOn (motive := fun _ => α) e (k 0) (fun n => k (Nat.succ n))

theorem force_eq {α : Sort u} (e : Nat) (k : Nat → α) : force e k = k e := by
  cases e <;> rfl

/-- field `j` of a packed vector -/
def fld (u j : Nat) : Nat := Nat.land (Nat.shiftRight u (Nat.mul 4 j)) 15

/-- greedy meld test, reading counts from `w`; `fuel` positions starting at `j`;
    `p0`/`p1` = sequences that still need a tile at the current / next position -/
noncomputable def grW (w : Nat → Nat) (lim : Nat) : Nat → Nat → Nat → Nat → Bool :=
  Nat.rec (motive := fun _ => Nat → Nat → Nat → Bool)
    (fun _ p0 p1 => Nat.beq p0 0 && Nat.beq p1 0)
    (fun _ ih j p0 p1 =>
      cond (Nat.blt (w j) p0) false
        (cond (Nat.blt j lim)
          (ih (Nat.succ j) (Nat.add p1 (Nat.mod (Nat.sub (w j) p0) 3)) (Nat.mod (Nat.sub (w j) p0) 3))
          (Nat.beq (Nat.mod (Nat.sub (w j) p0) 3) 0 && ih (Nat.succ j) p1 0)))

/-- the category vector `u` splits into melds -/
noncomputable def isM (len lim u : Nat) : Bool := grW (fld u) lim len 0 0 0

noncomputable def anyBelow (f : Nat → Bool) (n : Nat) : Bool :=
  Nat.rec (motive := fun _ => Bool) false (fun i ih => f i || ih) n

noncomputable def maskBelow (f : Nat → Bool) (n : Nat) : Nat :=
  Nat.rec (motive := fun _ => Nat) 0 (fun i ih => cond (f i) (Nat.lor (Nat.shiftLeft 1 i) ih) ih) n

/-- `u` splits into one pair plus melds -/
noncomputable def isP (len lim u : Nat) : Bool :=
  anyBelow (fun p => Nat.ble 2 (fld u p) &&
    force (Nat.sub u (Nat.shiftLeft 2 (Nat.mul 4 p))) (isM len lim)) len

/-- local mask of tiles `t` with `u + t` splitting into melds -/
noncomputable def wmL (len lim u : Nat) : Nat :=
  maskBelow (fun t => Nat.blt (fld u t) 4 &&
    force (Nat.add u (Nat.shiftLeft 1 (Nat.mul 4 t))) (isM len lim)) len

/-- local mask of tiles `t` with `u + t` splitting into a pair plus melds -/
noncomputable def wpL (len lim u : Nat) : Nat :=
  maskBelow (fun t => Nat.blt (fld u t) 4 &&
    force (Nat.add u (Nat.shiftLeft 1 (Nat.mul 4 t))) (isP len lim)) len

/-- all packed vectors with `npos` fields, each `≤ 4`, summing to `rem` -/
noncomputable def vecs : Nat → Nat → List Nat :=
  Nat.rec (motive := fun _ => Nat → List Nat)
    (fun rem => cond (Nat.beq rem 0) [0] [])
    (fun _ ih rem =>
      List.flatMap
        (fun d => cond (Nat.ble d rem) ((ih (Nat.sub rem d)).map (fun x => Nat.add d (Nat.mul 16 x))) [])
        [0, 1, 2, 3, 4])

noncomputable def anyL {α : Type} (f : α → Bool) (l : List α) : Bool :=
  List.rec (motive := fun _ => Bool) false (fun a _ ih => f a || ih) l

noncomputable def allL {α : Type} (f : α → Bool) (l : List α) : Bool :=
  List.rec (motive := fun _ => Bool) true (fun a _ ih => f a && ih) l

/-- bit 3 of each of the 34 fields -/
def guard : Nat := 0x8888888888888888888888888888888888

/-- SWAR sub-multiset test: every field of `c` is at most the corresponding field of `h`
    (valid when all fields are `≤ 4`) -/
def fits (c h : Nat) : Bool := Nat.beq (Nat.land (Nat.sub (Nat.add h guard) c) guard) guard

/-- an ordered 4-code `(t₀,t₁,t₂,t₃)` is stored as `t₀ + 64 t₁ + 64² t₂ + 64³ t₃` -/
def codeTile (e i : Nat) : Nat := Nat.mod (Nat.shiftRight e (Nat.mul 6 i)) 64

/-- the multiset of an encoded code, as a packed count vector -/
def codeVec (e : Nat) : Nat :=
  Nat.add (Nat.add (Nat.shiftLeft 1 (Nat.mul 4 (codeTile e 0))) (Nat.shiftLeft 1 (Nat.mul 4 (codeTile e 1))))
          (Nat.add (Nat.shiftLeft 1 (Nat.mul 4 (codeTile e 2))) (Nat.shiftLeft 1 (Nat.mul 4 (codeTile e 3))))

/-- binary search trees used as lookup tables -/
inductive PTree (β : Type) where
  | leaf : PTree β
  | node : PTree β → Nat → β → PTree β → PTree β

noncomputable def PTree.find {β : Type} (dflt : β) (t : PTree β) (x : Nat) : β :=
  PTree.rec (motive := fun _ => β) dflt
    (fun _ k v _ il ir => cond (Nat.blt x k) il (cond (Nat.beq x k) v ir)) t

/-- all (key, value) pairs of a tree -/
def PTree.toList {β : Type} : PTree β → List (Nat × β)
  | .leaf => []
  | .node l k v r => l.toList ++ (k, v) :: r.toList

end Tenpai
