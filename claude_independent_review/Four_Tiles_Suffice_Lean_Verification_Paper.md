# Four Tiles Suffice: A Kernel-Only, End-to-End Lean 4 Formalisation of the Optimal Encoding Length for Mahjong Wait Sets

**feierbuqiu**

20 October 2026

---

## Abstract

We present an end-to-end formal verification, in the Lean 4 proof assistant, of the answer to a combinatorial coding problem that arises from Japanese mahjong.

**The problem.** A player holds a 13-tile hand that is one tile away from winning (*tenpai*). Before play, the player and a partner agree on a rule. The player then arranges all thirteen tiles face down; the partner turns over *k* of them and must name the complete set of tiles that would complete the hand (its *wait set*). The question is the least *k* for which a single agreed rule works for every legal tenpai hand.

**Background.** An earlier computational study established, by exhaustive computation and an explicit construction, that this least value is *k*\* = 4. Its accompanying formal proof attempt, however, did not establish the result.

**Our approach.** We transcribe the problem statement into a 91-line Lean specification and prove the theorem `kStar_eq_four : IsKStar 4`.
- The proof uses the earlier study's encoding plan as an *untrusted certificate*.
- It reduces the coverage of every legal tenpai hand to finite checks whose meaning is itself proved in Lean.
- It discharges the 1,075 resulting checks by evaluation inside the Lean kernel, with no native code evaluation.

**Assurance.** The final theorem depends only on Lean's three standard axioms, a property enforced at build time by a fail-closed gate. A from-scratch build, bound to a SHA-256 manifest of the sources, completes in 21 minutes 38 seconds on a 16-thread workstation. Continuous integration repeats the complete check from scratch on GitHub's standard Linux runner (4 CPUs, 16 GB of RAM) whenever the Lean sources change; there it completes in 31 minutes 37 seconds.

**This paper.** We describe the kernel-oriented engineering that made a computation of this size feasible, an independent review and the changes it prompted, and the artefacts that let others reproduce the result locally or online.

**Keywords:** formal verification; Lean 4; proof by computation; kernel reduction; certificate checking; combinatorial coding; mahjong

---

## 1 Introduction

### 1.1 The problem

**Tiles and hands.** Japanese mahjong uses 34 tile types, with four physical copies of each:
- nine ranks in each of three suits (characters *m*, dots *p*, bamboos *s*);
- seven honour tiles.

A 13-tile hand *H* is *tenpai* when adding one more tile *t* produces a legal 14-tile winning hand. There are three winning shapes:
- four melds and a pair, where a meld is three of a kind or a run of three consecutive ranks within one suit;
- seven distinct pairs;
- the thirteen orphans.

The added tile *t* may not be a fifth copy of a type. The *wait set* of *H* is

&nbsp;&nbsp;&nbsp;&nbsp;*W*(*H*) = { *t* ∈ *T* : *c<sub>H</sub>*(*t*) < 4 and *H* ⊎ {*t*} ∈ 𝒢 },

where *c<sub>H</sub>*(*t*) is the number of copies of *t* in *H* and 𝒢 is the set of winning 14-tile multisets.

**The encoding game.** The puzzle was first posed in a Bilibili post by Lingzhi Shenpanzhe (Bilibili user 零之审判者; Lingzhi Shenpanzhe, 2026); the precise problem statement studied here is feierbuqiu (2026). It poses a cooperative game. Two parties agree on a protocol in advance:
1. The first party sees a tenpai hand *H* and lays all thirteen tiles face down in an order of their choosing.
2. The second party turns over *k* tiles at agreed positions and must then announce *W*(*H*) exactly.

**From protocols to a combinatorial form.** The statement proves that adaptive and fixed-position viewing have the same optimum (its §6). It then eliminates positions entirely (its §7):

&nbsp;&nbsp;&nbsp;&nbsp;*k*\* = min { *k* ∈ {0, …, 13} : ∃ *f* : ℋ → *T<sup>k</sup>*, ∀*H* *f*(*H*) ∈ *A<sub>k</sub>*(*H*), ∀*H*, *H*′ (*f*(*H*) = *f*(*H*′) ⇒ *W*(*H*) = *W*(*H*′)) },

where:
- ℋ is the set of legal 13-tile hands with a non-empty wait set;
- *A<sub>k</sub>*(*H*) is the set of ordered *k*-tuples that use no tile type more often than *H* contains it.

**Related puzzles.** The problem is a relative of Fitch Cheney's five-card trick, in which the choice and order of four shown cards identify a fifth (Chen et al., 2024; Kleber, 2002). Here, however:
- the message must determine a *set* of tiles rather than a single card;
- the "deck" is a multiset in which each tile type may occur up to four times.

### 1.2 The earlier computational result

The answer *k*\* = 4 was obtained in an earlier computational study by Qianwan Dangliang (2026), shared in reply to the original Bilibili post. That study established:
- **the lower bound *k*\* ≥ 4**, by a counting argument on the sub-universe *U* = {2m, …, 8m} of seven tile types. Hands drawn from *U* exhibit 347 distinct wait sets, but only 7³ = 343 ordered triples of tiles from *U* exist.
- **the upper bound *k*\* ≤ 4**, by an explicit plan that assigns ordered four-tile codes to each of the 2,846 wait classes (17,579 codes in total).

We adopt that study's computation, construction and conclusion as they stand. **We did not alter its solution process or its construction.** Our contribution is the formal proof.

The study also included a Lean development. Its definitions of feasibility and of a hand did not match the problem statement:
- codes could contain values outside the 34 tile types;
- hands were unconstrained arrays.

In addition, its large computations relied on native evaluation, which extends the trusted base to the compiler (Lean FRO, n.d.-c). For these reasons it does not constitute a formal proof of *k*\* = 4. The present work supplies one.

### 1.3 Contributions

1. **A faithful specification.**
   - A single 91-line file transcribes §2 and §7 of the problem statement.
   - It uses only Lean's core library and introduces none of the auxiliary notions (wait classes, code tables, decompositions) that the proof uses.
2. **A kernel-only, end-to-end proof** of `kStar_eq_four : IsKStar 4` in Lean 4.35.0, the latest stable release at the time of writing (Lean FRO, 2026).
   - It contains no `sorry`, no custom axioms and no native evaluation.
   - Every finite computation is checked by kernel reduction (`decide +kernel`).
3. **Engineering techniques for kernel-scale computation.** These include:
   - value-level memoisation through the kernel's evaluation cache;
   - packed bit-vector representations;
   - an enumeration scheme that avoids the cost of structurally recursive library functions under kernel reduction;
   - a cost-model-driven split of the computation into many small declarations.

   Each measure is supported by measurements, and they should transfer to other computational proofs in Lean.
4. **Release engineering for trust and reproducibility:**
   - a fail-closed axiom gate;
   - a from-scratch build bound to a source manifest;
   - an independent review whose findings were all adopted;
   - an artefact that regenerates byte-for-byte;
   - continuous integration that repeats the complete kernel check online whenever the Lean sources change.

### 1.4 Organisation

- Section 2 reviews the relevant background.
- Section 3 presents the specification.
- Section 4 describes the methodology.
- Section 5 reports the verification results and assesses their trustworthiness.
- Section 6 explains how to reproduce them.
- Section 7 summarises the work and discusses limitations and future directions.
- Section 8 concludes.

---

## 2 Background and Related Work

### 2.1 Lean 4 and its kernel

**The kernel.** Lean 4 is an interactive theorem prover and programming language based on dependent type theory (de Moura & Ullrich, 2021). Proofs produced by its elaborator and tactics are re-checked by a comparatively small *kernel*.

**Two ways to decide a proposition.** The `decide` tactic proves a decidable proposition by evaluating its decision procedure to `true`:
- The option `+kernel` performs this reduction in the kernel itself.
- `decide +native` (also available as `native_decide`) instead runs compiled code. Since Lean 4.29.0 it records each such computation as a dedicated axiom, and its correctness rests on the compiler and on all `@[implemented_by]` definitions (Lean FRO, n.d.-c).

**Axioms.** Lean's three standard axioms are `propext`, `Classical.choice` and `Quot.sound` (Avigad et al., n.d.; Lean FRO, n.d.-c). The command `#print axioms` lists the axioms on which a constant transitively depends. Any axiom beyond these three indicates a custom axiom, `sorryAx` indicates an incomplete proof, and names containing `_native` indicate native evaluation (Lean FRO, n.d.-c).

**Testing messages.** The command `#guard_msgs` checks that the messages produced by a command match an expected text exactly (Lean FRO, n.d.-b).

### 2.2 Proofs by computation

The idea of letting a proof checker run a verified decision procedure, so-called reflection, is well established (Boutin, 1997). Landmark computer-assisted results have been formally verified with substantial computational components:
- the four colour theorem in Coq (Gonthier, 2008);
- the Kepler conjecture in HOL Light and Isabelle (Hales et al., 2017).

Large combinatorial results have also been settled by a separate search whose output is then checked by an independent, simpler checker (Heule et al., 2016).

Our work follows the same principle: the search that produced the encoding plan lies outside the trusted base, and only its output is checked. All of the checking happens inside the Lean kernel itself; no external checker and no compiled code is involved.

### 2.3 Card tricks and mahjong combinatorics

**Card tricks.** Kleber (2002) analysed the five-card trick and its optimal deck size. Chen et al. (2024) studied card tricks from an information-theoretic viewpoint, including decks with repeated cards.

**Mahjong.** Cheng et al. (2019) studied the mathematics of mahjong hands, including counts of single-suit hands. Our independent census agrees with their published single-suit figures (Section 4.6).

We are not aware of earlier work on the wait-set encoding problem itself.

---

## 3 Formal Specification

### 3.1 Design principles

The trusted statement is the single file [`Tenpai/Spec.lean`](lean_formal/lean_project/Tenpai/Spec.lean) (Appendix A). It was written against the problem statement, line by line, under three rules:
1. it imports nothing beyond Lean's core library;
2. every definition corresponds to a clause of §2 or §7 of the statement;
3. the definitions are stated for readability, not for computation, so that no efficiency concern can distort their meaning.

### 3.2 Definitions

| Problem statement | Lean definition |
|---|---|
| 34 tile types *T* | `Tile := Fin 34` (0–8 characters, 9–17 dots, 18–26 bamboos, 27–33 honours) |
| hand as a multiset | `Counts := Tile → Nat` |
| meld | `Meld.seq t` or `Meld.trip t`; `Meld.Valid (.seq t) := t.val < 27 ∧ t.val % 9 ≤ 6` |
| four melds and a pair | ∃ pair *p* and melds *m*₁…*m*₄, all valid, with the counts equal **exactly** to the sum |
| seven pairs | ∃ `S : List Tile`, `S.Nodup ∧ S.length = 7 ∧ ∀ s, G s = if s ∈ S then 2 else 0` |
| thirteen orphans | ∃ orphan *o*, `G s = [s is an orphan] + [s = o]` |
| winning set 𝒢 | `IsWinning G := (∀ s, G s ≤ 4) ∧ (IsStandard G ∨ IsSevenPairs G ∨ IsKokushi G)` |
| wait set *W*(*H*) | `W H t := H t < 4 ∧ IsWinning (addTile H t)` |
| inputs ℋ | `InH H := (total H = 13 ∧ ∀ t, H t ≤ 4) ∧ ∃ t, W H t` |
| admissible messages *A<sub>k</sub>*(*H*) | `Admissible H v := ∀ t, (List.finRange k).countP (fun j => v j = t) ≤ H t` |
| feasibility | `Feasible k := ∃ f : {H // InH H} → (Fin k → Tile), (∀ H, Admissible H.1 (f H)) ∧ ∀ H H', f H = f H' → W H.1 = W H'.1` |
| optimum *k*\* | `IsKStar n := n ≤ 13 ∧ Feasible n ∧ ∀ k, k ≤ 13 → Feasible k → n ≤ k` |

### 3.3 Fidelity

Each rule of the statement has a visible counterpart:
- **Runs stay within a suit, and honours never form runs.** Enforced by `Meld.Valid`.
- **Four copies of one type do not count as two pairs.** Enforced by `S.Nodup` together with exact counts.
- **No winning multiset has more than four copies of a type, and a fifth copy cannot be a wait.** Enforced by `∀ s, G s ≤ 4` and by `H t < 4` respectively.
- **Every legal tenpai hand is an input.** Enforced by the universal quantification over `{H // InH H}`.
- **Messages are ordered and respect stock.** Enforced by `Fin k → Tile` with the multiplicity bound in `Admissible`.
- **Equal messages force equal wait sets.** Expressed by `f H = f H' → W H.1 = W H'.1`.
- **No computability or uniformity requirement is added.** As in §7, `f` is an arbitrary function.

The exact multiset decomposition in `IsStandard` already forces a total of 14 tiles, so no separate cardinality clause is needed. An independent review reached the same assessment (Section 5.5).

---

## 4 Methodology

### 4.1 Architecture of the proof

```
Spec.lean (trusted statement)
   │  semantic bridges, proved once:
   │    greedy meld test ⇔ meld decomposition (Greedy, Melds)
   │    standard waits factor by suit (Std);  34-bit wait mask ⇔ W H t (Waits)
   ▼
finite checks: Bool functions over packed data (Checks, Enum)
   │  soundness lemmas: "check = true ⇒ property" (CheckSound, CheckSound2, EnumSound)
   ▼
1,075 leaf theorems `… = true := by decide +kernel` (Run/*), evaluated by the kernel
   │  assembly: prefix trees, shape ranges, case analysis (Main, Cover*, Final, Lower)
   ▼
theorem kStar_eq_four : IsKStar 4   +   fail-closed axiom gate
```

The proof has two halves. `not_feasible_le3` shows that no *k* ≤ 3 is feasible, and `feasible_four` shows that *k* = 4 is. The theorem `kstar_of_checks` combines them, given the results of the finite checks.

### 4.2 Lower bound

**Witnesses.** The lower bound uses 347 witness hands whose tiles all lie in *U* = {2m, …, 8m}. A single kernel check (`witOK`) confirms three things:
- each witness is a legal 13-tile hand;
- each has a non-empty wait set;
- the computed wait masks are strictly increasing, and hence pairwise distinct.

**Counting.** Any admissible message for such a hand uses only tiles from *U*, so at most 7<sup>*k*</sup> ≤ 343 < 347 distinct messages exist for *k* ≤ 3. By the pigeonhole principle, two witnesses with different wait sets would share a message. This contradicts decodability.

The argument is proved for each *k* ≤ 3 directly, without any monotonicity assumption. It is the counting argument of the earlier study (Qianwan Dangliang, 2026); the witness list was produced by our own independent computation (*Duli fuhe baogao*, 2026).

### 4.3 Upper bound by certificate checking

**Encoding.** The encoding function selects, for each hand, a code of the hand's wait class that is contained in the hand as a multiset. Two lemmas connect the code representation to the specification:
- `admissible_of_fits` turns the packed containment test into the multiplicity bound of `Admissible`;
- `validCode` and `tupleOf_inj` ensure that integer codes correspond one-to-one to four-tuples of tiles.

The selection is made with `Classical.choose`, which is the source of the `Classical.choice` axiom. The theorem therefore asserts that such a function *exists*, which is exactly what §7 requires; no executable encoder is certified.

**Decoding.** A decoding table maps each ordered code to a wait mask. The kernel check `decodeOK` confirms that every code of every class maps back to that class. Equal messages therefore imply equal wait sets.

**Coverage.** The central theorem, `cover`, states that every hand in ℋ contains some code of its own class. The proof first establishes semantic bridges:
- correctness of a greedy meld-decomposition test (`grW_correct`, `isM_iff`, `meldDec_iff_isM`);
- factorisation of standard waits by suit (`std_wait_iff`);
- bit-for-bit agreement between a computed 34-bit wait mask and the specification (`wAll_correct`).

It then shows, by case analysis, that every hand falls into one of seven families, each discharged by one finite check (Table 1).

The decomposition into an *active* part and inert melds, the use of codes contained in the active part, the special rule for the 217 four-tile exceptional units, and the five-group pigeonhole for seven pairs are the earlier study's construction ideas. We adopt them unchanged.

*Table 1. The case analysis behind the coverage theorem.*

| Family of hands | Finite check | Size of the check |
|---|---|---|
| thirteen-orphans waits | K: every thirteen-orphans configuration checked directly | 169 (*o*, *t*) combinations |
| no standard wait (seven pairs only) | T3: the six pairs fall into ≤ 5 consecutive groups; two pairs share a group, and a code lies within the single tile plus those two pairs | 34 × C(33, 2) pairs |
| single-tile wait | T0: a code lies within the tile plus any meld of another suit | 34 tiles × melds |
| one active suit | T1: a code lies within the active part (four-tile parts may use the meld rule instead) | 411,408 vectors |
| two active suits | T2: a code lies within the two active parts (meld rule when they total four tiles) | 5,094,402 units |
| one active suit, also seven-pairs shaped | T4A: direct check | 529,501 hands in T4A and T4B together, with 29,574 plan look-ups |
| two active suits, also seven-pairs shaped | T4B: direct check | (included above) |

### 4.4 Kernel-scale computation

Kernel reduction is substitution-based and caches every term it evaluates while it checks a declaration. The measures below were each introduced in response to a measured bottleneck.

**Primitive representations.**
- All loops are written with the recursors `Nat.rec` and `List.rec`.
- Arithmetic uses the kernel's built-in big-number operations.
- Count vectors are packed four bits per tile type into a single natural number, so that a code's containment in a hand is one guarded subtraction and mask, a SWAR test across all 34 fields at once.
- Look-up tables are binary search trees.

**Memoisation by value.** A combinator `force e k := Nat.casesOn e (k 0) (fun n => k (n+1))` makes the kernel evaluate `e` to a literal before applying `k`. The kernel's evaluation cache then acts as a memo table keyed by value. This lets meld-decomposition results for suit vectors be shared across hands.

**Avoiding structurally recursive library functions.**
- The problem: core list functions such as `List.map`, `List.flatMap` and `List.drop` are defined by structural recursion, and the kernel must reduce through their encodings. In our measurements, merely traversing the list of all 93,600 thirteen-tile suit vectors exceeded 10 GB of memory, and so did a single `drop 30000`.
- The replacement: we introduced `allVecs`, a prefix-recursive enumerator. It fixes the lowest fields of a vector one at a time and builds no list, so chunks of the enumeration are simply subtrees. Its relationship to the reference enumeration is proved (`allVecs_iff`, `allVecs_node`).
- The small inner lists of T2 are built with `List.rec`-based helpers that are proved equal to the library functions.
- For T4, a range-restricted shape loop `forShapesR` splits the check by hand shape; `forShapes_of_R` reassembles the full domain.

**Splitting and scheduling.**
- *Splitting.* Because the kernel's cache grows with the work done in a single declaration and is released afterwards, large checks were split into 1,075 leaf declarations. A cost model, calibrated on isolated runs, sizes each leaf at about 12 s of kernel time; for example, a T1 leaf of 3,535 vectors took 12.6 s and peaked at 1.7 GB. Leaves were packed into 96 modules arranged as six independent import chains, which caps the number of concurrent Lean processes at six.
- *A failed first attempt.* The first full run chunked lists by index and ran eight processes of about 5 GB each. It drove the machine's commit charge to 68.7 of 69.2 GB and was stopped. The redesign above replaced it.

### 4.5 Data and provenance

**The plan.** The earlier study's final plan ([`plan_k4_final.json`](../third_party/qianwan-dangliang/work/verify/plan_k4_final.json), SHA-256 `b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163`, matching the hash distributed with it) was read by format only and converted to Lean literals:
- a class tree with 2,846 classes and 17,579 codes;
- a decoding tree.

Codes were reordered *within* each class by usefulness, solely to shorten kernel look-ups. We confirmed that every class's code list is unchanged as a multiset and that no class contains duplicates.

**Other data.**
- The 347 lower-bound witnesses and the seven-pairs group boundaries are likewise data.
- All data and all 1,075 leaf statements are produced by generator scripts. These are outside the trusted base: a wrong datum can only make a check fail, never make a false theorem pass.
- Regenerating every data and leaf file from the inputs reproduces the published files byte for byte.

### 4.6 Independent cross-check of the computational result

Before formalising, we independently re-derived the earlier study's principal results with our own implementation, which shares no code with the original (*Duli fuhe baogao*, 2026):
- **Exhaustive census.** Our census enumerated all 92,371,838 tenpai hands and their 2,846 wait classes. Two independent wait-set implementations agreed on every hand, and our single-suit figures agree with those published by Cheng et al. (2019).
- **Lower bound.** Three independent implementations confirmed the counts 7,875, 5,628 and 347.
- **A distinct construction.** We built an encoding plan of our own (11,123 ordered codes). Both it and the original plan were checked against every one of the 92,371,838 hands, with no failures.

Our programs and their recorded outputs are published in [`src/`](src/) and [`out/`](out/). The computation and the conclusion of the earlier study withstood this independent scrutiny. The present paper is concerned with the formal proof.

### 4.7 Use of AI assistance

The formalisation was carried out with the assistance of Claude Opus 5.5 (Anthropic, 2026b) operating within Claude Code (Anthropic, 2026a). The human investigators:
- defined the task;
- set the requirements (pure-kernel checking, latest toolchain, strict scope);
- made the key decisions on scope and direction;
- reviewed the outcomes.

The Lean kernel is the safeguard for correctness: AI-written definitions are reviewed against the problem statement, and AI-written proofs are accepted only if the kernel checks them. Details are given in the Declaration of Generative AI Use.

---

## 5 Verification and Results

### 5.1 Main theorem and axiom footprint

The development ends with the following, after which the build prints the theorem's axiom list:

```lean
theorem kStar_eq_four : IsKStar 4 :=
  kstar_of_checks classTree decodeTree cutsOf witnesses checked decode_ok wit_ok wit_len

/-- info: 'Tenpai.kStar_eq_four' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Tenpai.kStar_eq_four
```

The axiom footprint is `[propext, Classical.choice, Quot.sound]`, that is, Lean's standard axioms only. A scan of all 126 source files finds:
- no use of `sorry` (the word occurs only in the explanatory comment of the gate), and no `admit`, `native_decide`, `ofReduceBool`, `implemented_by`, `extern`, `unsafe`, custom axiom, elaborator extension or macro;
- one option only, `maxHeartbeats 0`, set on each leaf. It disables the time-out but not the kernel check.

### 5.2 Build statistics

The authoritative build was run from scratch on 20 October 2026, in a fresh copy of the sources with no build cache. The machine ran Windows 11 with 16 logical cores and 32 GB of RAM, using Lean 4.35.0 (commit `eb6cafb`) and Lake 5.0.0.

*Table 2. Kernel time by check family. Module times are apportioned to leaves by estimated cost.*

| Family | Leaves | Kernel time (process-seconds) |
|---|---|---|
| T1 | 284 | ≈ 1,770 |
| T2 | 732 | ≈ 4,430 |
| T4 (A and B) | 53 | ≈ 780 |
| decoding, T0, T3, K, witnesses | 6 | ≈ 90 |
| **Total** | **1,075** | **7,066 (≈ 2.0 h)** |

- **Wall-clock time:** 21 minutes 38 seconds, from 10:49:49 to 11:11:27 local time.
- **Module times:** each of the 96 check modules took between 17 and 110 seconds (median 74 s). The assembly module, with 323 theorems, took 5.2 seconds.
- **Memory:** combined peak 11.8 GB; peak for a single process 4.8 GB.
- **Earlier build:** an earlier build of the same sources, made before the acceptance gate was appended to [`Main.lean`](lean_formal/lean_project/Tenpai/Main.lean), took 22 minutes 11 seconds.
- **Online build:** the continuous-integration build of Section 6.5 ran from scratch on GitHub's standard Linux runner (Ubuntu 24.04, 4 CPUs, 16 GB of RAM) on 20 October 2026. It completed in 31 minutes 37 seconds, with a combined memory peak of 9.5 GB (5.0 GB for a single process), the same source digest and the same axiom footprint.

### 5.3 Acceptance gate and negative tests

Because `#guard_msgs` requires an exact match, the build *fails* if the final theorem's axiom list differs in any way from the three standard axioms (Lean FRO, n.d.-b). A `sorry` anywhere in the dependency cone would add `sorryAx`, and a custom axiom would be listed by name. A successful build is therefore itself the release check. Table 3 records the tests of this gate.

*Table 3. Tests of the acceptance gate.*

| Test | Reported axioms | Outcome |
|---|---|---|
| a theorem proved with `sorry` | `[sorryAx]` | error, exit code 1 |
| a theorem using an extra axiom `cheat : False` | `[cheat]` | error, exit code 1 |
| a theorem using only standard axioms (`Classical.em`) | `[propext, Classical.choice, Quot.sound]` | accepted |
| a complete project generated in the generator's stub mode | `[propext, sorryAx, Classical.choice, Quot.sound]` | `lake build` fails at the gate |

### 5.4 Binding the evidence to the sources

A manifest tool records the SHA-256 digest of every source file and a combined digest of the set. It uses the same algorithm as the independent review, so the two can be compared directly.

- **Before and after.** The digest of the 126 Lean sources was identical before and after the authoritative build: `a179bd53953a21dc4b38489f9cc13e10c698a23b034555ae413b85e68ef191d2`. It equals the digest of the distributed copy.
- **Relation to the reviewed snapshot.** Compared with the snapshot examined by the independent review (`dd200c59…8278f`), exactly one file differs: `Main.lean`, to which the gate of Section 5.3 was appended.

### 5.5 Independent review

An independent, separately operated AI agent performed a static source-level review of the project (*Lean duli jingtai shenyue*, 2026). It concluded that:
- the specification matches the problem statement;
- the chain from definitions to the final theorem is complete;
- no additional trust entry point exists.

It raised three non-blocking findings, all of which we adopted:
- **R1.** A statement in our earlier internal report extended the claim from "the original plan is a valid certificate and *k*\* = 4" to "the original study's whole computational process is correct". We narrowed it. The theorem certifies the plan and the optimum, not every program that produced them.
- **R2.** A successful build was not fail-closed, because the generator retained a stub mode that emits `sorry`. We added the gate of Section 5.3 and labelled stub output.
- **R3.** Existing build logs were not bound to a fixed source version. We performed the hash-bound, from-scratch build of Sections 5.2 and 5.4.

The review also noted a scope boundary, discussed in Section 7.3.

### 5.6 Trustworthiness

**Trusted base.** The result depends on:
- the Lean 4.35.0 kernel;
- the 91-line specification;
- the core-library definitions it uses (`Fin`, `List.finRange`, `List.countP`, `List.Nodup`, `List.sum`);
- the integrity of the toolchain binaries.

Everything else is checked rather than trusted: the plan, the tables, the 1,075 generated leaves, the generators, our census programs and the original study's verification scripts.

**Threats to validity and their mitigations:**
1. **Kernel soundness.** The kernel is small and widely used. An independent re-check with a second kernel implementation remains possible; see Section 7.4.
2. **Specification fidelity.** This is the main human-judged step. It was addressed by line-by-line comparison with the statement, by our own review and by the independent review (Section 5.5), and the specification is short enough to be read in full (Appendix A).
3. **Toolchain integrity.** The toolchain is the official release, pinned in `lean-toolchain`.
4. **Environment.** Kernel checking does not depend on timing or scheduling. Three complete builds produced the same result: two on Windows and one on Linux in continuous integration (Section 5.2).
5. **Scope.** See Section 7.3.

**Overall assessment.** The statement *k*\* = 4, as defined in §7 of the problem statement, holds with the assurance of a machine-checked proof whose trusted base is the Lean kernel and a short specification.

---

## 6 Reproducibility

### 6.1 Artefact

The artefact is the folder [`claude_independent_review/lean_formal/`](lean_formal/), with four parts:

| Part | Contents |
|---|---|
| [`lean_project/`](lean_formal/lean_project/) | 126 Lean files: the root module [`Tenpai.lean`](lean_formal/lean_project/Tenpai.lean), 23 hand-written modules (about 5,000 lines), 4 [data modules](lean_formal/lean_project/Tenpai/Data/), 97 [generated check modules](lean_formal/lean_project/Tenpai/Run/) and the generated assembly [`Main.lean`](lean_formal/lean_project/Tenpai/Main.lean); plus [`lakefile.toml`](lean_formal/lean_project/lakefile.toml), [`lean-toolchain`](lean_formal/lean_project/lean-toolchain) and [`lake-manifest.json`](lean_formal/lean_project/lake-manifest.json) |
| [`tools/`](lean_formal/tools/) | generators, the split planner and its cost model, the manifest tool and analysis utilities |
| [`logs/`](lean_formal/logs/) | logs of the authoritative, earlier and online builds, the source manifests, the gate tests and calibration measurements |
| [`ci/`](lean_formal/ci/) | the workflow template from which the repository's continuous integration was derived (Section 6.5) |

### 6.2 Local reproduction

With the toolchain manager elan installed (Lean FRO, n.d.-a), run:

```bash
cd claude_independent_review/lean_formal/lean_project
lake build
```

- The pinned toolchain (Lean 4.35.0) is installed automatically.
- Success means the gate has passed. The build log then contains `'Tenpai.kStar_eq_four' depends on axioms: [propext, Classical.choice, Quot.sound]` and ends with `Build completed successfully`.
- Expect about 22 minutes on a 16-thread, 32 GB machine. Peak memory is about 12 GB in total, and about 5 GB for one process.

### 6.3 Verifying source identity

```bash
python -I claude_independent_review/lean_formal/tools/manifest.py claude_independent_review/lean_formal/lean_project out.json
```

The field `lean_set_sha256` must equal `a179bd53953a21dc4b38489f9cc13e10c698a23b034555ae413b85e68ef191d2`.

### 6.4 Regenerating the data and the checks

Starting from the original plan file and our witness certificate:
1. [`tools/gen_data.py`](lean_formal/tools/gen_data.py) regenerates the four data modules;
2. `tools/plan_split.exe`, compiled from [`tools/plan_split.c`](lean_formal/tools/plan_split.c), regenerates the split plan;
3. [`tools/gen_split.py`](lean_formal/tools/gen_split.py) regenerates the 97 check modules and `Main.lean`.

The output is byte-identical to the distributed files (102 files compared, none differing). Appendix B lists the commands.

### 6.5 Online reproduction

Three complementary routes support re-execution by others:
1. **Continuous integration.**
   - The workflow [`.github/workflows/lean-kernel-build.yml`](../.github/workflows/lean-kernel-build.yml), adapted from the template [`ci/lean-kernel-build.yml`](lean_formal/ci/lean-kernel-build.yml), runs on GitHub Actions whenever the Lean sources change. It checks the source digest, installs the pinned toolchain, runs `lake build` from scratch, so that the acceptance gate of Section 5.3 decides the outcome, and keeps the log, timing and memory samples.
   - It uses GitHub's standard Linux runner for public repositories, which provides 4 CPUs and 16 GB of RAM (GitHub, n.d.). The [run](https://github.com/feierbuqiu/mahjong-tenpai-proof/actions/runs/39360643654) of 20 October 2026 completed the build in 31 minutes 37 seconds with a combined memory peak of 9.5 GB, which confirms that the six-chain configuration fits this runner. Its log is kept in [`logs/ci_build/`](lean_formal/logs/ci_build/).
   - A second workflow, [`.github/workflows/integrity.yml`](../.github/workflows/integrity.yml), checks on every change that the third-party mirror is byte-for-byte unchanged and that the Lean sources match the recorded digest.
   - GitHub's runner for private repositories provides only 2 CPUs and 8 GB. There the checks would have to be regenerated with fewer chains, which changes the source digest.
2. **Archiving.** Depositing the artefact with a long-term archive that issues persistent identifiers (for example Zenodo, https://zenodo.org, or Software Heritage, https://www.softwareheritage.org) would let readers cite the exact version together with its digest.
3. **External re-checking.** Lean's documentation describes tools that replay stored declarations through the kernel (`lean4checker`) or compare them using the official kernel and the independent checker nanoda (Bailey, n.d.; Lean FRO, n.d.-c). Because our proof uses no native evaluation, it is eligible for such re-checking.

---

## 7 Summary of Work and Future Directions

### 7.1 Work completed

1. **Toolchain.** We upgraded to the latest stable Lean release, 4.35.0, with no dependencies beyond the core library.
2. **Specification.** We wrote the 91-line specification and checked it clause by clause against the problem statement.
3. **Semantic layer.** We proved the semantic layer in about 5,000 lines:
   - greedy meld test correctness;
   - per-suit factorisation of standard waits;
   - correctness of the 34-bit wait mask;
   - the active/inert case analysis;
   - the coverage theorem;
   - the upper bound and the lower bound;
   - the combination theorem `kstar_of_checks`.
4. **Data.** We converted the original plan into Lean data, reordering codes only within classes and verifying that the code multisets are unchanged.
5. **Kernel engineering.** We diagnosed and removed kernel-scale bottlenecks: memoisation by value, packed representations, prefix-tree enumeration in place of structurally recursive list functions, and cost-model-driven splitting into 1,075 leaves. Each step was guided by isolated measurements, including a failed first full run.
6. **Generation and assembly.** We generated and assembled the leaves (prefix-tree joins, shape-range merges) and completed the end-to-end kernel build.
7. **Trust and evidence.** After the independent review, we added the fail-closed axiom gate and its tests. We bound a from-scratch build to a source manifest and narrowed the scope of our claims.
8. **Packaging and continuous integration.** We packaged the artefact for local reproduction and set up continuous integration that repeats the complete kernel check online.

### 7.2 Lessons

- **Kernel cost is per declaration.** The cost of kernel reduction is dominated by the terms retained within one declaration. Splitting work across declarations bounds memory, and three consecutive declarations in one file peaked no higher than one.
- **Structural recursion is expensive in the kernel.** Library functions defined by structural recursion are costly under kernel reduction at scale. Hand-written recursor-based loops and enumerators that build no intermediate lists avoid this.
- **A gate makes success meaningful.** A build that cannot succeed unless the axiom footprint is exactly as stated turns build success into a meaningful acceptance criterion.

### 7.3 Limitations

1. **The physical protocols are not formalised.** The theorem concerns the combinatorial form of §7. The equivalence between the two physical viewing protocols (§6 of the problem statement), and their identification with §7, rest on the statement's prose proofs.
2. **No executable encoder.** The encoding function is shown to exist; no executable encoder is certified.
3. **The original programs are not verified.** The theorem certifies the original plan as a certificate and the optimum *k*\* = 4. It does not certify the programs, intermediate statistics or construction history of the earlier study (cf. finding R1).
4. **The data conversion is not formalised.** The conversion of the original JSON plan into Lean literals is not itself formalised. The theorem is about the Lean constants, whose identity with the original plan was confirmed by external comparison (Section 4.5).
5. **Rule variants are out of scope.** These include red fives, or allowing four copies of one type to count as two pairs.

### 7.4 Future work

1. **Formalise the viewing protocols.** Formalise both physical protocols of §§4–6 and their equivalence with §7, so that the result covers the physical game directly.
2. **Replay with an independent kernel.** Replay the development in a second kernel implementation, such as nanoda via Lean's comparison tooling (Bailey, n.d.; Lean FRO, n.d.-c).
3. **Formalise the census figures.** Prove in Lean the exact number of wait classes (2,846) and the exact number of tenpai hands (92,371,838).
4. **Extract a verified encoder and decoder.**
5. **Study rule variants.** Investigate how the optimum changes under rule variants.
6. **Contribute kernel-friendly libraries.** Package the kernel-friendly enumeration and memoisation techniques as reusable components.

---

## 8 Conclusion

We have given a complete, kernel-only Lean 4 proof that four tiles suffice, and that fewer do not, for communicating the full wait set of any legal tenpai hand.
- The proof rests on a short, readable specification and on Lean's standard axioms.
- It checks the earlier study's encoding plan as a certificate rather than trusting the programs that produced it.
- It is fail-closed by construction, reproducible from a hash-identified artefact, and re-checked online by continuous integration.

The work confirms, by a machine-checked proof, the answer that the earlier computational study had found.

---

## Acknowledgements

**The original puzzle and study.** We gratefully acknowledge Lingzhi Shenpanzhe (Bilibili user 零之审判者), who posed the original puzzle on Bilibili (Lingzhi Shenpanzhe, 2026), and Qianwan Dangliang (Bilibili user 千万当量), the author of the earlier computational study (Qianwan Dangliang, 2026). The study carried out the computation, devised the construction and reached the result *k*\* = 4. Our contribution is confined to the formal proof. We did not modify the original solution process or construction. Our only change to the original data was to reorder codes within each class, for efficiency, leaving every class's code set unchanged.

**AI assistance.** We acknowledge the substantial contribution of Anthropic's Claude Code (Anthropic, 2026a), and in particular of the Claude Opus 5.5 model (Anthropic, 2026b). Almost all of the formalisation was developed with its assistance: the specification, the proofs, the kernel-performance engineering, the generators and build tooling, and the drafting of this paper. It was an indispensable tool throughout.

**Independent review.** We also thank the independent AI review (*Lean duli jingtai shenyue*, 2026). Its findings substantially improved the rigour of our claims and of the release process.

---

## Declaration of Generative AI Use

**Tools.** Claude Code (Anthropic, 2026a), running the model Claude Opus 5.5 (model identifier `claude-opus-5-5`; Anthropic, 2026b), was used throughout the project.

**Uses:**
- writing and revising the Lean specification and proofs;
- writing the data generators, the split planner and the analysis scripts;
- designing, running and monitoring builds, and diagnosing performance problems;
- performing the independent cross-check computations of Section 4.6;
- drafting this paper.

**Human oversight.** The human investigators defined the problem and the requirements, set the scope, approved the approach at each stage and reviewed the outputs. Technical choices within that scope were proposed and implemented with the AI system.

**Safeguards.** The correctness of every proof was established by the Lean kernel, not by the AI system. The specification was reviewed against the problem statement by the investigators and by an independent AI review (*Lean duli jingtai shenyue*, 2026), conducted by a separately operated agent.

**Responsibility.** The investigators take full responsibility for the content of this paper.

---

## Data and Code Availability

All sources, data, generators, logs and the workflow template are contained in the artefact [`claude_independent_review/lean_formal/`](lean_formal/) (Section 6.1). The continuous-integration workflows are in [`.github/workflows/`](../.github/workflows/).

All of it is published at <https://github.com/feierbuqiu/mahjong-tenpai-proof>. The original computational package (Qianwan Dangliang, 2026) is mirrored there, unmodified, under [`third_party/qianwan-dangliang/`](../third_party/qianwan-dangliang/). Its final plan is the file [`third_party/qianwan-dangliang/work/verify/plan_k4_final.json`](../third_party/qianwan-dangliang/work/verify/plan_k4_final.json) (SHA-256 `b95f5523bae86db71fabd62380fb6820b3d83c4e794eb92043b7ca8f4fa57163`).

---

## References

Anthropic. (2026a). *Claude Code* [Computer software]. https://claude.com/product/claude-code

Anthropic. (2026b). *Claude Opus 5.5* [Large language model]. https://www.anthropic.com/claude/opus

Avigad, J., de Moura, L., Kong, S., & Ullrich, S. (n.d.). Axioms and computation. In *Theorem proving in Lean 4*. Retrieved October 20, 2026, from https://lean-lang.org/theorem_proving_in_lean4/Axioms-and-Computation/

Bailey, C. (n.d.). *nanoda_lib* [Computer software]. GitHub. Retrieved October 20, 2026, from https://github.com/ammkrn/nanoda_lib

Boutin, S. (1997). Using reflection to build efficient and certified decision procedures. In M. Abadi & T. Ito (Eds.), *Theoretical aspects of computer software* (pp. 515–529). Springer. https://doi.org/10.1007/BFb0014565

Chen, A., Cummins, T., De Francesco, R., Greene, J., Khovanova, T., Meng, A., Parida, T., Pulugurtha, A., Swaroop, A., & Tsui, S. (2024). *Card tricks and information* (arXiv:2405.21007) [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2405.21007

Cheng, Y., Li, C.-K., & Li, S. H. (2019). *Mathematical aspect of the combinatorial game "Mahjong"* (arXiv:1707.07345v2) [Preprint]. arXiv. https://doi.org/10.48550/arXiv.1707.07345

de Moura, L., & Ullrich, S. (2021). The Lean 4 theorem prover and programming language. In A. Platzer & G. Sutcliffe (Eds.), *Automated deduction – CADE 28* (pp. 625–635). Springer. https://doi.org/10.1007/978-3-030-79876-5_37

*Duli fuhe baogao: Dai Bing wenti (er)—"zui shao fan 4 zhang" shifou chengli* [Independent re-verification report: The Dai–Bing problem (II)—Do four tiles at minimum suffice?] [Unpublished report]. (2026).

feierbuqiu. (2026). *The Dai–Bing problem (II): Permutation encoding of tenpai wait information* [Problem statement, translated from the Chinese original]. GitHub. https://github.com/feierbuqiu/mahjong-tenpai-proof/blob/main/docs/problem-statement.md

GitHub. (n.d.). *GitHub-hosted runners reference*. GitHub Docs. Retrieved October 20, 2026, from https://docs.github.com/en/actions/reference/runners/github-hosted-runners

Gonthier, G. (2008). Formal proof—The four-color theorem. *Notices of the American Mathematical Society, 55*(11), 1382–1393. https://www.ams.org/notices/200811/tx081101382p.pdf

Hales, T., Adams, M., Bauer, G., Dang, T. D., Harrison, J., Hoang, L. T., Kaliszyk, C., Magron, V., McLaughlin, S., Nguyen, T. T., Nguyen, Q. T., Nipkow, T., Obua, S., Pleso, J., Rute, J., Solovyev, A., Ta, T. H. A., Tran, N. T., Trieu, T. D., . . . Zumkeller, R. (2017). A formal proof of the Kepler conjecture. *Forum of Mathematics, Pi, 5*, Article e2. https://doi.org/10.1017/fmp.2017.1

Heule, M. J. H., Kullmann, O., & Marek, V. W. (2016). Solving and verifying the Boolean Pythagorean triples problem via cube-and-conquer. In N. Creignou & D. Le Berre (Eds.), *Theory and applications of satisfiability testing – SAT 2016* (pp. 228–245). Springer. https://doi.org/10.1007/978-3-319-40970-2_15

Kleber, M. (2002). The best card trick. *The Mathematical Intelligencer, 24*(1), 9–11. https://doi.org/10.1007/BF03025305

*Lean duli jingtai shenyue: Si zhang bianma jielun ji duan dao duan yanzheng lian* [Independent static review of the Lean formalisation: The four-tile result and its end-to-end verification chain] [Unpublished report]. (2026).

Lean FRO. (n.d.-a). *elan: The Lean version manager* [Computer software]. GitHub. Retrieved October 20, 2026, from https://github.com/leanprover/elan

Lean FRO. (n.d.-b). Interacting with Lean. In *The Lean language reference* (Lean 4.35.0). Retrieved October 20, 2026, from https://lean-lang.org/doc/reference/4.35.0/Interacting-with-Lean/

Lean FRO. (n.d.-c). Validating a Lean proof. In *The Lean language reference* (Lean 4.35.0). Retrieved October 20, 2026, from https://lean-lang.org/doc/reference/4.35.0/ValidatingProofs/

Lean FRO. (2026). *Lean 4* (Version 4.35.0) [Computer software]. GitHub. https://github.com/leanprover/lean4/releases/tag/v4.35.0

Lingzhi Shenpanzhe [零之审判者]. (2026, September). [Mahjong tenpai wait-encoding puzzle] [Post]. Bilibili. https://www.bilibili.com/opus/1246853448736964611

Qianwan Dangliang [千万当量]. (2026). *Majiang "fan pai cai tingpai" zuizhong baogao: Python zhengming lian + Lean xingshihua jinzhan* [Final report on the mahjong "turn over tiles to guess the waits" problem: Python proof chain and Lean formalisation progress] [Report and software package]. Baidu Netdisk. https://pan.baidu.com/s/1qdCW0N75TZzIRsUYx-75Tw?pwd=utfx

---

## Appendix A. The Trusted Specification (`Tenpai/Spec.lean`)

```lean
/-!
# 呆饼问题（二）：听牌信息的排列编码问题 — formal problem statement

This file is the whole trusted statement.  It follows §2 and §7 of
「呆饼问题（二）：听牌信息的排列编码问题.md」 line by line and uses nothing but
Lean core.  Every other file of the development only *proves* things about
these definitions.

Tile numbering (§2.1):
  `0–8` = 1m…9m, `9–17` = 1p…9p, `18–26` = 1s…9s, `27–33` = E S W N P F C.
-/

namespace Tenpai

/-- §2.1  the 34 tile types `T` -/
abbrev Tile := Fin 34

/-- a multiset of tiles, given by its multiplicity function `c_H` -/
abbrev Counts := Tile → Nat

/-- `∑_{t ∈ T} c_H(t)` -/
def total (H : Counts) : Nat := ((List.finRange 34).map H).sum

/-- §2.2  a meld (面子): a sequence of three consecutive number tiles of one suit (顺子),
    or three tiles of one type (刻子) -/
inductive Meld where
  | seq  (t : Tile)   -- the tiles t, t+1, t+2
  | trip (t : Tile)   -- the tiles t, t, t

/-- a sequence must start at rank 1–7 of a number suit, so that it stays inside the suit;
    honours never form sequences -/
def Meld.Valid : Meld → Prop
  | .seq t  => t.val < 27 ∧ t.val % 9 ≤ 6
  | .trip _ => True

/-- multiplicity of tile `s` in a meld -/
def Meld.count : Meld → Tile → Nat
  | .seq t,  s => if s.val = t.val ∨ s.val = t.val + 1 ∨ s.val = t.val + 2 then 1 else 0
  | .trip t, s => if s = t then 3 else 0

/-- §2.2 (1)  standard form: four melds plus one pair (雀头), as a multiset decomposition -/
def IsStandard (G : Counts) : Prop :=
  ∃ (p : Tile) (m₁ m₂ m₃ m₄ : Meld), m₁.Valid ∧ m₂.Valid ∧ m₃.Valid ∧ m₄.Valid ∧
    ∀ s, G s = (if s = p then 2 else 0) + m₁.count s + m₂.count s + m₃.count s + m₄.count s

/-- §2.2 (2)  seven pairs: exactly seven distinct tile types, two copies each
    (four copies of one type never count as two pairs) -/
def IsSevenPairs (G : Counts) : Prop :=
  ∃ S : List Tile, S.Nodup ∧ S.length = 7 ∧ ∀ s, G s = if s ∈ S then 2 else 0

/-- the 13 terminal and honour types (幺九牌与字牌): 1 and 9 of each suit, and the 7 honours -/
def IsOrphan (t : Tile) : Prop :=
  (t.val < 27 ∧ (t.val % 9 = 0 ∨ t.val % 9 = 8)) ∨ 27 ≤ t.val

instance : DecidablePred IsOrphan := fun t => by unfold IsOrphan; infer_instance

/-- §2.2 (3)  thirteen orphans: one of each of the 13 types plus a second copy of one of them -/
def IsKokushi (G : Counts) : Prop :=
  ∃ o, IsOrphan o ∧ ∀ s, G s = (if IsOrphan s then 1 else 0) + (if s = o then 1 else 0)

/-- §2.2  the set `𝒢` of legal 14-tile winning multisets (no type more than 4 times) -/
def IsWinning (G : Counts) : Prop :=
  (∀ s, G s ≤ 4) ∧ (IsStandard G ∨ IsSevenPairs G ∨ IsKokushi G)

/-- `H ⊎ {t}` -/
def addTile (H : Counts) (t : Tile) : Counts := fun s => if s = t then H s + 1 else H s

/-- §2.3  the wait set `W(H) = { t ∈ T : c_H(t) < 4 ∧ H ⊎ {t} ∈ 𝒢 }` -/
def W (H : Counts) : Tile → Prop := fun t => H t < 4 ∧ IsWinning (addTile H t)

/-- a legal 13-tile hand (§2.1) -/
def IsHand (H : Counts) : Prop := total H = 13 ∧ ∀ t, H t ≤ 4

/-- §2.3  the set `ℋ` of all admissible inputs: legal 13-tile hands with `W(H) ≠ ∅` -/
def InH (H : Counts) : Prop := IsHand H ∧ ∃ t, W H t

/-- §7  `A_k(H)`: ordered k-tuples that use no tile more often than `H` contains it -/
def Admissible (H : Counts) {k : Nat} (v : Fin k → Tile) : Prop :=
  ∀ t, (List.finRange k).countP (fun j => v j = t) ≤ H t

/-- §7  `k` is feasible: there is `f : ℋ → T^k` with `f(H) ∈ A_k(H)` such that
    `f(H) = f(H') ⇒ W(H) = W(H')` -/
def Feasible (k : Nat) : Prop :=
  ∃ f : {H // InH H} → (Fin k → Tile),
    (∀ H, Admissible H.1 (f H)) ∧ ∀ H H', f H = f H' → W H.1 = W H'.1

/-- §7  `n = k* = min { k ∈ {0,…,13} : k feasible }` -/
def IsKStar (n : Nat) : Prop :=
  n ≤ 13 ∧ Feasible n ∧ ∀ k, k ≤ 13 → Feasible k → n ≤ k

end Tenpai
```

---

## Appendix B. Commands and Expected Output

| Purpose | Command (from `claude_independent_review/`) | Expected result |
|---|---|---|
| full kernel build | `cd lean_formal/lean_project && lake build` | the line `'Tenpai.kStar_eq_four' depends on axioms: [propext, Classical.choice, Quot.sound]`, then `Build completed successfully` |
| source identity | `python -I lean_formal/tools/manifest.py lean_formal/lean_project out.json` | `lean_set_sha256` = `a179bd53…191d2` |
| regenerate data | `python -I lean_formal/tools/gen_data.py lean_formal/tools/plan_k4_reordered.txt out/u7_certificate.txt lean_formal/lean_project` | four data modules, byte-identical |
| regenerate the split plan | `cd lean_formal/lean_project && ../tools/plan_split.exe ../tools/split.txt 12` | [`split.txt`](lean_formal/tools/split.txt), byte-identical |
| regenerate the checks | `cd lean_formal/lean_project && python -I ../tools/gen_split.py ../tools/split.txt 6` | 97 check modules and `Main.lean`, byte-identical |

---

## Appendix C. Artefact Inventory

| Path (under `lean_formal/`) | Contents |
|---|---|
| [`lean_project/Tenpai/Spec.lean`](lean_formal/lean_project/Tenpai/Spec.lean) | trusted specification (91 lines) |
| `lean_project/Tenpai/`: [`Basic`](lean_formal/lean_project/Tenpai/Basic.lean), [`Packed`](lean_formal/lean_project/Tenpai/Packed.lean), [`Greedy`](lean_formal/lean_project/Tenpai/Greedy.lean), [`Melds`](lean_formal/lean_project/Tenpai/Melds.lean), [`Loops`](lean_formal/lean_project/Tenpai/Loops.lean), [`Std`](lean_formal/lean_project/Tenpai/Std.lean), [`Waits`](lean_formal/lean_project/Tenpai/Waits.lean), [`Shape`](lean_formal/lean_project/Tenpai/Shape.lean) | computational core; meld-test and wait-mask correctness |
| `lean_project/Tenpai/`: [`Checks`](lean_formal/lean_project/Tenpai/Checks.lean), [`CheckSound`](lean_formal/lean_project/Tenpai/CheckSound.lean), [`CheckSound2`](lean_formal/lean_project/Tenpai/CheckSound2.lean), [`Enum`](lean_formal/lean_project/Tenpai/Enum.lean), [`EnumSound`](lean_formal/lean_project/Tenpai/EnumSound.lean) | finite checks and their soundness |
| `lean_project/Tenpai/`: [`Glue`](lean_formal/lean_project/Tenpai/Glue.lean), [`Glue2`](lean_formal/lean_project/Tenpai/Glue2.lean), [`Cover0`](lean_formal/lean_project/Tenpai/Cover0.lean), [`Cover`](lean_formal/lean_project/Tenpai/Cover.lean), [`Cover2`](lean_formal/lean_project/Tenpai/Cover2.lean), [`Cover3`](lean_formal/lean_project/Tenpai/Cover3.lean), [`Cover4`](lean_formal/lean_project/Tenpai/Cover4.lean) | coverage theorem |
| `lean_project/Tenpai/`: [`Lower`](lean_formal/lean_project/Tenpai/Lower.lean), [`Final`](lean_formal/lean_project/Tenpai/Final.lean) | lower bound, upper bound, `kstar_of_checks` |
| [`lean_project/Tenpai/Data/`](lean_formal/lean_project/Tenpai/Data/) | plan, decoding table, seven-pairs groups, 347 witnesses (generated) |
| [`lean_project/Tenpai/Run/`](lean_formal/lean_project/Tenpai/Run/) | 1,075 kernel-checked leaves in 96 modules, plus an aggregator (generated) |
| [`lean_project/Tenpai/Main.lean`](lean_formal/lean_project/Tenpai/Main.lean) | assembly, `kStar_eq_four` and the acceptance gate (generated) |
| [`tools/`](lean_formal/tools/) | [`gen_data.py`](lean_formal/tools/gen_data.py), [`gen_split.py`](lean_formal/tools/gen_split.py), [`plan_split.c`](lean_formal/tools/plan_split.c), [`manifest.py`](lean_formal/tools/manifest.py), [`timing.py`](lean_formal/tools/timing.py), analysis utilities |
| [`logs/clean_build/`](lean_formal/logs/clean_build/) | authoritative from-scratch build: log, timing, memory samples, source manifests before and after, axiom printout |
| [`logs/first_build/`](lean_formal/logs/first_build/), [`logs/gate_tests/`](lean_formal/logs/gate_tests/), [`logs/calibration_runs.txt`](lean_formal/logs/calibration_runs.txt) | earlier build, gate tests, calibration runs |
| [`logs/ci_build/`](lean_formal/logs/ci_build/) | the online build: runner details, log, timing, memory samples, source manifest |
| [`ci/lean-kernel-build.yml`](lean_formal/ci/lean-kernel-build.yml) | GitHub Actions workflow template, adapted as the repository's continuous integration |
