import Tenpai.Waits

/-!
# The finite checks run by the kernel

Every check is a `Bool` computation over packed vectors; `CheckSound.lean` proves what each
one means.  The plan is passed as `tree : PTree (List Nat)` (wait mask ↦ encoded codes).
-/

namespace Tenpai

/-! ## the plan -/

/-- codes of class `W` (memoised by value) -/
noncomputable def classCodes (tree : PTree (List Nat)) (W : Nat) : List Nat := force W (PTree.find [] tree)

/-- some code of class `W` is a sub-multiset of the packed hand `h` -/
noncomputable def hasCode (tree : PTree (List Nat)) (W h : Nat) : Bool :=
  anyL (fun e => fits (codeVec e) h) (classCodes tree W)

/-- an encoded code is four tiles `< 34` -/
def validCode (e : Nat) : Bool :=
  Nat.blt e 16777216 && Nat.blt (codeTile e 0) 34 && Nat.blt (codeTile e 1) 34 &&
    Nat.blt (codeTile e 2) 34 && Nat.blt (codeTile e 3) 34

/-- decoding table check: every code of every class decodes to that class -/
noncomputable def decodeOK (tree : PTree (List Nat)) (dtree : PTree Nat) : Bool :=
  allL (fun p => allL (fun e => Nat.beq (dtree.find 0 e) p.1 && validCode e) p.2) tree.toList

/-! ## melds as packed vectors -/

def unitV (t : Nat) : Nat := Nat.shiftLeft 1 (Nat.mul 4 t)
def tripV (t : Nat) : Nat := Nat.mul 3 (unitV t)
def seqV (t : Nat) : Nat := Nat.add (unitV t) (Nat.add (unitV (Nat.succ t)) (unitV (Nat.succ (Nat.succ t))))
def seqOK (t : Nat) : Bool := Nat.blt t 27 && Nat.ble (Nat.mod t 9) 6

/-- all melds whose category `t / 9` is allowed by the bit mask `cats` -/
noncomputable def meldList (cats : Nat) : List Nat :=
  (List.range 34).flatMap (fun t =>
    cond (Nat.testBit cats (Nat.div t 9)) (tripV t :: cond (seqOK t) [seqV t] []) [])

/-- all categories except `k` / except `x` and `y` -/
def catsExcept (k : Nat) : Nat := Nat.xor 15 (Nat.shiftLeft 1 k)
def catsExcept2 (x y : Nat) : Nat := Nat.xor (catsExcept x) (Nat.shiftLeft 1 y)

/-- every field at most 4 -/
noncomputable def le4 (h : Nat) : Bool := allBelow (fun t => Nat.ble (fld h t) 4) 34

/-- exception rule for a 4-tile active part `A` whose 9 inert tiles are three melds:
    either one meld already completes a code, or the three melds together do -/
noncomputable def meldRule (tree : PTree (List Nat)) (W A cats : Nat) : Bool :=
  let bad := (meldList cats).filter (fun m => !(hasCode tree W (Nat.add A m)))
  allL (fun m1 => allL (fun m2 => allL (fun m3 =>
      !(le4 (Nat.add (Nat.add (Nat.add A m1) m2) m3)) ||
      hasCode tree W (Nat.add (Nat.add (Nat.add A m1) m2) m3)) bad) bad) bad

/-! ## T0: single waits (tanki) -/

noncomputable def t0ok (tree : PTree (List Nat)) : Bool :=
  allBelow (fun z => allL (fun m => hasCode tree (Nat.shiftLeft 1 z) (Nat.add (unitV z) m))
    (meldList (catsExcept (Nat.div z 9)))) 34

/-! ## T1: one active category -/

noncomputable def t1unit (tree : PTree (List Nat)) (k n u : Nat) : Bool :=
  force (Nat.shiftLeft (cWP k u) (Nat.mul 9 k)) (fun W =>
    Nat.beq W 0 || hasCode tree W (Nat.shiftLeft u (Nat.mul 36 k)) ||
      (Nat.beq n 4 && meldRule tree W (Nat.shiftLeft u (Nat.mul 36 k)) (catsExcept k)))

/-! ## T2: two active categories -/

structure Inf where
  pk : Nat
  p : Bool
  wm : Nat

noncomputable def infOf (k u : Nat) : Inf :=
  ⟨Nat.shiftLeft u (Nat.mul 36 k), force u (cP k), Nat.shiftLeft (force u (cWM k)) (Nat.mul 9 k)⟩

def relevant (i : Inf) : Bool := i.p || !(Nat.beq i.wm 0)

noncomputable def t2pair (tree : PTree (List Nat)) (cats nsum : Nat) (a b : Inf) : Bool :=
  force (Nat.lor (cond b.p a.wm 0) (cond a.p b.wm 0)) (fun W =>
    Nat.beq W 0 || hasCode tree W (Nat.add a.pk b.pk) ||
      (Nat.beq nsum 4 && meldRule tree W (Nat.add a.pk b.pk) cats))

noncomputable def t2ok (tree : PTree (List Nat)) (x y nx ny : Nat) (us : List Nat) : Bool :=
  allL (fun u => !(relevant (infOf x u)) ||
      allL (t2pair tree (catsExcept2 x y) (Nat.add nx ny) (infOf x u))
        (((vecs (catLen y) ny).map (infOf y)).filter relevant)) us

/-- the same check with the roles of the two categories swapped (outer loop over `y`) -/
noncomputable def t2okRev (tree : PTree (List Nat)) (x y nx ny : Nat) (vs : List Nat) : Bool :=
  allL (fun v => !(relevant (infOf y v)) ||
      allL (fun a => t2pair tree (catsExcept2 x y) (Nat.add nx ny) a (infOf y v))
        (((vecs (catLen x) nx).map (infOf x)).filter relevant)) vs

/-! ## T3: seven pairs only — pigeonhole over five groups -/

/-- the group of tile `t` for single `z`: number of cut points `≤ t` -/
noncomputable def grpOf (cuts : List Nat) (t : Nat) : Nat := countL (fun c => Nat.ble c t) cuts
where countL (f : Nat → Bool) (l : List Nat) : Nat :=
  List.rec (motive := fun _ => Nat) 0 (fun a _ ih => Nat.add (cond (f a) 1 0) ih) l

noncomputable def t3ok (tree : PTree (List Nat)) (cutsOf : Nat → List Nat) : Bool :=
  allBelow (fun z => Nat.ble (cutsOf z).length 4 && allBelow (fun x => allBelow (fun y =>
      !(Nat.blt x y) || Nat.beq x z || Nat.beq y z ||
      !(Nat.beq (grpOf (cutsOf z) x) (grpOf (cutsOf z) y)) ||
      hasCode tree (Nat.shiftLeft 1 z) (Nat.add (unitV z) (Nat.add (Nat.mul 2 (unitV x)) (Nat.mul 2 (unitV y)))))
    34) 34) 34

/-! ## T4: hands that are standard tenpai *and* seven-pairs shaped -/

/-- packed vectors with `npos` fields `≤ d` summing to `rem` -/
noncomputable def vecsD (d : Nat) : Nat → Nat → List Nat :=
  Nat.rec (motive := fun _ => Nat → List Nat)
    (fun rem => cond (Nat.beq rem 0) [0] [])
    (fun _ ih rem =>
      List.flatMap
        (fun c => cond (Nat.ble c rem) ((ih (Nat.sub rem c)).map (fun x => Nat.add c (Nat.mul 16 x))) [])
        (List.range (Nat.succ d)))

noncomputable def singles (len v : Nat) : Nat := countBelow (fun j => Nat.beq (fld v j) 1) len

/-- candidate category vectors: fields `≤ 2`, at most one single, total `n` -/
noncomputable def cand (k n : Nat) : List Nat := (vecsD 2 (catLen k) n).filter (fun v => Nat.ble (singles (catLen k) v) 1)

def sel4 (a b c d : Nat) : Nat → Nat := fun k => cond (Nat.beq k 0) a (cond (Nat.beq k 1) b (cond (Nat.beq k 2) c d))

/-- the candidate list of category `k` with `n` tiles, active or inert (inert ones must be melds);
    memoised by the value of `n` -/
noncomputable def t4list (act : Bool) (k n : Nat) : List Nat :=
  force n (fun n' => cond act (cand k n') ((cand k n').filter (cM k)))

/-- number of single tiles of a hand -/
noncomputable def singTotal (cv : Nat → Nat) : Nat :=
  Nat.add (Nat.add (force (cv 0) (singles 9)) (force (cv 1) (singles 9)))
          (Nat.add (force (cv 2) (singles 9)) (force (cv 3) (singles 7)))

/-- the single tiles of a hand, as a mask -/
noncomputable def singBits (cv : Nat → Nat) : Nat :=
  orBelow (fun k => Nat.shiftLeft (force (cv k) (fun v => maskBelow (fun j => Nat.beq (fld v j) 1) (catLen k)))
    (Nat.mul 9 k)) 4

/-- one active category `x`: the class is the active wait mask plus the single -/
noncomputable def t4handA (tree : PTree (List Nat)) (x : Nat) (cv : Nat → Nat) : Bool :=
  !(Nat.beq (singTotal cv) 1) || Nat.beq (force (cv x) (cWP x)) 0 ||
    hasCode tree (Nat.lor (Nat.shiftLeft (force (cv x) (cWP x)) (Nat.mul 9 x)) (singBits cv)) (glue cv)

/-- the standard wait mask of two active categories `x`, `y` -/
noncomputable def maskB2 (x y : Nat) (cv : Nat → Nat) : Nat :=
  Nat.lor (cond (force (cv y) (cP y)) (Nat.shiftLeft (force (cv x) (cWM x)) (Nat.mul 9 x)) 0)
          (cond (force (cv x) (cP x)) (Nat.shiftLeft (force (cv y) (cWM y)) (Nat.mul 9 y)) 0)

/-- two active categories `x`, `y` -/
noncomputable def t4handB (tree : PTree (List Nat)) (x y : Nat) (cv : Nat → Nat) : Bool :=
  !(Nat.beq (singTotal cv) 1) || Nat.beq (maskB2 x y cv) 0 ||
    hasCode tree (Nat.lor (maskB2 x y cv) (singBits cv)) (glue cv)

/-- all hands of one size shape, given which categories are active and the per-hand check -/
noncomputable def t4shape (act : Nat → Bool) (n : Nat → Nat) (chk : (Nat → Nat) → Bool) : Bool :=
  allL (fun a => allL (fun b => allL (fun c => allL (fun d => chk (sel4 a b c d))
    (t4list (act 3) 3 (n 3))) (t4list (act 2) 2 (n 2))) (t4list (act 1) 1 (n 1))) (t4list (act 0) 0 (n 0))

/-- shape with one active category `x` -/
noncomputable def shape1 (x : Nat) (n : Nat → Nat) : Bool :=
  Nat.beq (Nat.mod (n x) 3) 1 && Nat.ble 4 (n x) &&
    allL (fun k => Nat.beq k x || Nat.beq (Nat.mod (n k) 3) 0) [0, 1, 2, 3]

/-- shape with two active categories `x`, `y` -/
noncomputable def shape2 (x y : Nat) (n : Nat → Nat) : Bool :=
  Nat.beq (Nat.mod (n x) 3) 2 && Nat.beq (Nat.mod (n y) 3) 2 &&
    allL (fun k => Nat.beq k x || Nat.beq k y || Nat.beq (Nat.mod (n k) 3) 0) [0, 1, 2, 3]

/-- all shapes `n0 + n1 + n2 + n3 = 13` -/
noncomputable def forShapes (p : (Nat → Nat) → Bool) : Bool :=
  allBelow (fun n0 => allBelow (fun n1 => allBelow (fun n2 =>
    !(Nat.ble (Nat.add n0 (Nat.add n1 n2)) 13) || p (sel4 n0 n1 n2 (Nat.sub 13 (Nat.add n0 (Nat.add n1 n2)))))
    14) 14) 14

noncomputable def t4okA (tree : PTree (List Nat)) (x : Nat) : Bool :=
  forShapes (fun n => !(shape1 x n) || t4shape (fun k => Nat.beq k x) n (t4handA tree x))

noncomputable def t4okB (tree : PTree (List Nat)) (x y : Nat) : Bool :=
  forShapes (fun n => !(shape2 x y n) || t4shape (fun k => Nat.beq k x || Nat.beq k y) n (t4handB tree x y))

/-! ## K: thirteen-orphans hands -/

/-- `O + o - t` as a count function -/
def kokF (o t : Nat) : Nat → Nat := fun s =>
  if s < 34 then (if isOrphB s = true then 1 else 0) + (if s = o then 1 else 0) - (if s = t then 1 else 0) else 0

noncomputable def kokCv (o t : Nat) : Nat → Nat := fun k => pkF (catF (kokF o t) k) (catLen k)

noncomputable def kOK (tree : PTree (List Nat)) : Bool :=
  allBelow (fun o => allBelow (fun t => !(isOrphB o) || !(isOrphB t) ||
    hasCode tree (wAll (kokCv o t)) (glue (kokCv o t))) 34) 34

/-! ## lower-bound witnesses (all tiles in 2m … 8m) -/

noncomputable def mOnly (u : Nat) : Nat → Nat := fun k => cond (Nat.beq k 0) u 0

noncomputable def sumFields (v n : Nat) : Nat := Nat.rec (motive := fun _ => Nat) 0 (fun j ih => Nat.add ih (fld v j)) n

/-- a witness: fields only at positions 1–7, each `≤ 4`, thirteen tiles -/
noncomputable def witValid (u : Nat) : Bool :=
  Nat.blt u (Nat.shiftLeft 1 36) && Nat.beq (fld u 0) 0 && Nat.beq (fld u 8) 0 &&
    allBelow (fun j => Nat.ble (fld u j) 4) 9 && Nat.beq (sumFields u 9) 13

noncomputable def strictInc : List Nat → Bool
  | [] => true
  | [_] => true
  | a :: b :: l => Nat.blt a b && strictInc (b :: l)

noncomputable def witOK (ws : List Nat) : Bool :=
  allL witValid ws && allL (fun u => !(Nat.beq (wAll (mOnly u)) 0)) ws &&
    strictInc (ws.map (fun u => wAll (mOnly u)))

end Tenpai
