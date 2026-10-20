# Proof Overview

This is a short guide to the Lean development in [`claude_independent_review/lean_formal/lean_project/`](../claude_independent_review/lean_formal/lean_project/). Sections 3–5 of the [paper](../claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md) give the full account.

## The statement

The trusted statement is [`Tenpai/Spec.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Spec.lean): 91 lines, Lean core only, transcribing the problem's definitions and its combinatorial form (Section 1.1 of the [paper](../claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md)). Its header comment names the document it was transcribed from; the definitions are those of the paper. The final theorem is

```lean
theorem Tenpai.kStar_eq_four : Tenpai.IsKStar 4
```

where `IsKStar n` says three things:
- `n ≤ 13`;
- `n` tiles are feasible;
- no smaller `k ≤ 13` is feasible.

**Feasibility** of *k* means there is a function sending every legal tenpai hand to an ordered *k*-tuple of its own tiles, such that equal tuples imply equal wait sets.

## The two halves

| Half | Theorem | Idea |
|---|---|---|
| **Lower bound** | `not_feasible_le3` ([`Lower.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Lower.lean)) | 347 witness hands using only tiles 2m–8m have pairwise distinct wait sets (one kernel check). Any message for them uses only 7 tile types, so at most 7³ = 343 messages exist for *k* ≤ 3, and two witnesses would collide. |
| **Upper bound** | `feasible_four` ([`Final.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Final.lean)) | Encode each hand by a code of its wait class that the hand contains. A decoding-table check shows that codes determine classes. The coverage theorem `cover` ([`Cover4.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Cover4.lean)) shows that every hand contains a code of its class. |

`kstar_of_checks` ([`Final.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Final.lean)) combines the two halves. `kStar_eq_four` ([`Main.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Main.lean)) instantiates it with the concrete data and the 1,075 kernel-checked leaves.

## From the specification to finite checks

The coverage theorem is reduced to finite computations in three layers.

1. **Semantic bridges**, proved once:
   - the greedy meld test is correct (`grW_correct`, `isM_iff`, `meldDec_iff_isM`);
   - standard waits factor by suit (`std_wait_iff`);
   - a computed 34-bit wait mask agrees bit for bit with the specification's `W H t` (`wAll_correct`).
2. **A case analysis** sorts every hand into one of seven families. Each family is discharged by one Boolean check:

   | Check | Family |
   |---|---|
   | K | thirteen orphans |
   | T3 | seven pairs only |
   | T0 | single-tile waits |
   | T1 | one active suit |
   | T2 | two active suits |
   | T4A / T4B | standard waits on a seven-pairs-shaped hand |

3. **Soundness lemmas** ([`CheckSound.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/CheckSound.lean), [`CheckSound2.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/CheckSound2.lean), [`EnumSound.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/EnumSound.lean)) prove what each check means when it returns `true`.

## Kernel-scale computation

Every check is proved by `decide +kernel`, that is, by evaluation inside the Lean kernel. Native code evaluation is not used anywhere.

To make this feasible, the development:
- uses only recursors (`Nat.rec`, `List.rec`) and the kernel's built-in arithmetic;
- packs hands into natural numbers, four bits per tile type;
- memoises by value through the kernel's evaluation cache (`force`);
- replaces core list functions with a prefix-recursive enumerator (`allVecs`);
- splits the work into 1,075 leaf declarations.

The leaves are generated into [`Tenpai/Run/`](../claude_independent_review/lean_formal/lean_project/Tenpai/Run/) and assembled in [`Tenpai/Main.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Main.lean).

## The acceptance gate

[`Main.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Main.lean) ends with

```lean
/-- info: 'Tenpai.kStar_eq_four' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Tenpai.kStar_eq_four
```

so the build fails unless the final theorem depends on exactly Lean's three standard axioms. A `sorry` anywhere in the final theorem's dependency cone would add `sorryAx`, and an extra axiom there would be listed by name. Declarations that the final theorem does not use are outside the gate's scope.

## Trusted base

The result depends on:
- the Lean 4.35.0 kernel;
- [`Spec.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Spec.lean);
- the few core-library definitions that `Spec.lean` uses.

Everything else lies outside the trusted base. The plan, the tables and the generated leaves are checked by the kernel. The generators, the cross-check programs and the original author's programs are not themselves verified; the proof checks only the properties of their outputs that it needs.
