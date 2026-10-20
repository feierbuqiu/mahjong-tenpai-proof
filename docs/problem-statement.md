# The Dai–Bing Problem (II): Permutation Encoding of Tenpai Wait Information

> **Author of this formulation:** feierbuqiu. This is an English translation of the author's [Chinese original](呆饼问题（二）：听牌信息的排列编码问题.md) (research version of 19 October 2026, a draft giving the definitions and the equivalence proof).
>
> **Origin of the puzzle:** the puzzle was first posed in a Bilibili post: <https://www.bilibili.com/opus/1246853448736964611>. This document makes the puzzle's inputs, permitted operations, outputs, quantifiers and optimality requirement precise. It defines the two viewing models, *adaptive one-by-one viewing* and *pre-fixed-position viewing*, and proves them equivalent.
>
> **Status of the original document:** as written, it gives a rigorous definition of the problem and a proof that the two viewing models are equivalent. It does **not** claim that the optimum is 4.
>
> **Note added in translation (20 October 2026):** the value *k*\* = 4 has since been established by a kernel-checked Lean 4 proof; see the [paper](../claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md). The Lean specification [`Tenpai/Spec.lean`](../claude_independent_review/lean_formal/lean_project/Tenpai/Spec.lean) transcribes §2 and §7 of this document.

Section numbers follow the original, because the Lean specification and the paper refer to them.

---

## 1. The puzzle for non-specialists

**The tiles.** A standard set of Japanese (riichi) mahjong tiles is used: **34 tile types, four copies of each, 136 tiles in total**. The following are ignored:
- flower tiles;
- open melds (chii, pon, kan);
- red fives;
- scoring patterns (yaku) and scoring values (han);
- any other game history.

Each tile is distinguished only by its type; the four physical copies of a type are indistinguishable.

**The players.** A computer gives the player **Dai** a hand of **exactly 13 tiles that is already tenpai**. A hand is tenpai when there is at least one tile type, with a physical copy still available, whose addition forms a legal 14-tile winning shape. A hand may wait on several types. For example, it may wait on both 3-characters and 6-characters; it may be a thirteen orphans hand waiting on all thirteen terminals and honours; or it may be a pure nine gates hand with a nine-sided wait.

Dai sees all 13 tiles and knows the complete set of waits. The other player, **Bing**, sees none of the tile faces. *Before* the game, the two may jointly agree on a rule of any complexity, provided it applies uniformly to all inputs. Then:

1. **Arrangement.** Dai may only rearrange **the original 13 tiles** into 13 fixed positions on the table, labelled 1 to 13, all face down. Dai may not add, remove, replace or mark tiles. Nor may Dai convey information by any other means: orientation, spacing, timing of placement, sounds, facial expressions and the like.
2. **Departure.** After placing the tiles, Dai leaves. Bing sees only 13 indistinguishable tile backs and the fixed position labels.
3. **Viewing.** Following the agreed rule, Bing turns over at most *k* tiles and reports **the set of all valid waiting tile types**. Bing does not need to recover the tiles that stay face down, nor the whole hand.
4. **Correctness.** Whichever legal 13-tile tenpai hand the computer deals, the report must be **exactly correct**. Missing waits and extra waits are both failures, and being correct with high probability is not a substitute for guaranteed correctness.

**Question: what is the least number *k* of tiles to be turned over for which an encoding and decoding protocol meeting these requirements can be designed?**

Here *encoding* means that Dai conveys information through **the order of the tile types**, and *decoding* means that Bing recovers the complete wait set from the **tile types seen, and their positions**, in a bounded number of views. The tile backs carry no distinguishing marks.

Two viewing modes are considered:

- **Model A, adaptive sequential viewing.** Bing may turn over a first tile, then choose where to look next based on what has been seen, and so on.
- **Model B, pre-fixed-position viewing.** Before seeing any tile face, Bing must fix, by the joint agreement, the *k* positions to be turned over. Bing then reads the tiles at those positions and does not change positions in response to what is seen.

## 2. Basic mathematical objects

### 2.1 Tile types and physical stock

The set of tile types is

```math
T = \{1m, \ldots, 9m,\; 1p, \ldots, 9p,\; 1s, \ldots, 9s,\; E, S, W, N, P, F, C\}, \qquad |T| = 34,
```

where:
- $`m`$, $`p`$, $`s`$ are the characters, dots and bamboos suits;
- the seven honour symbols stand for East, South, West, North, White, Green and Red.

A hand is a multiset $`H`$ over $`T`$; the multiplicity of tile type $`t`$ is written $`c_H(t)`$. An admissible 13-tile hand satisfies

```math
\sum_{t \in T} c_H(t) = 13, \qquad 0 \le c_H(t) \le 4 \quad (t \in T).
```

The four physical copies of a tile type carry no extra numbering, marks or readable differences.

### 2.2 Legal 14-tile winning shapes

Let $`\mathcal G`$ be the union of the following three classes of **14-tile multisets**, in each of which no tile type may occur more than four times:

1. **Standard form.** Four melds plus a pair (jantou).
   - Each meld is either three consecutive number tiles of one suit (a sequence, shuntsu) or three tiles of one type (a triplet, koutsu).
   - The pair is two tiles of one type.
   - The decomposition is taken as a multiset; the order of the melds is irrelevant.
2. **Seven pairs.** Exactly seven mutually distinct tile types, each occurring twice. Four copies of one type may not be counted as two pairs.
3. **Thirteen orphans.** One tile of each of the thirteen terminal and honour types, plus a second copy of one of them. The thirteen types are the 1 and the 9 of each number suit, and the seven honours.

Here *winning* refers only to the **combinatorial shape** of the tiles. It does not decide, from a concrete game state, whether a win by discard or by self-draw is allowed, or whether the hand has enough scoring value. The nine gates shape is naturally included in the standard form and needs no separate fourth class.

### 2.3 The wait set

For a 13-tile hand $`H`$, define its **set of valid waits**

```math
W(H) = \{\, t \in T : c_H(t) < 4 \ \land\ H \uplus \{t\} \in \mathcal G \,\}.
```

Here $`H \uplus \{t\}`$ denotes the hand with one more tile of type $`t`$ added. The constraint $`c_H(t) \lt 4`$ excludes a non-existent fifth copy of a type.

Define the set of **all admissible inputs**

```math
\mathcal H = \Bigl\{\, H : \sum_{t \in T} c_H(t) = 13,\ \forall t\ 0 \le c_H(t) \le 4,\ W(H) \ne \varnothing \,\Bigr\}.
```

Success must be guaranteed for every $`H \in \mathcal H`$. That hands are "dealt at random" only describes how an instance is chosen; it introduces no probability distribution and does not weaken the universal quantifier.

**The output is $`W(H)`$, not $`H`$ itself.** Two completely different hands with the same wait set may produce the same encoded message.

#### Examples of wait sets

- If $`W(H) = \{3m, 6m\}`$, both 3-characters and 6-characters must be reported.
- The thirteen-sided thirteen orphans wait corresponds to the set of all 13 terminal and honour types.
- The basic 13-tile nine gates shape $`1112345678999`$ (in one suit) corresponds to the nine-sided wait on $`1`$ to $`9`$.
- If $`c_H(6m) = 4`$, then $`6m \notin W(H)`$. This holds even if, in some formulation that ignores stock, $`6m`$ would appear to complete a shape: a fifth 6-characters may not be invented.

**Avoiding a misreading.** The standard 13-tile base of the pure nine gates nine-sided wait above does not itself contain four 6-characters. "Four 6-characters in hand exclude 6-characters" is an example of the general stock constraint, not an instance of that same pure nine gates hand.

## 3. The common encoding stage

Let $`\operatorname{Perm}(H)`$ be the set of all distinct ordered arrangements of length 13 of the multiset $`H`$. Dai and Bing may agree in advance on a **deterministic encoding function**

```math
E : \mathcal H \longrightarrow T^{13}, \qquad E(H) \in \operatorname{Perm}(H) \quad (\forall H \in \mathcal H).
```

For input $`H`$, Dai places $`E(H)_i`$ at position $`i`$, all face down. The function may not covertly introduce channels outside the tiles, nor change multiplicities. Dai then leaves.

Dai may compute $`H`$ and $`W(H)`$ in advance and choose the encoding accordingly. Bing knows the function $`E`$ and all decoding rules in advance, but does not know the current input $`H`$ before turning tiles over.

## 4. Model A: adaptive one-by-one viewing

**The decision rule.** Given an upper bound $`k`$ on the number of views, Bing fixes a deterministic decision rule in advance:

- the first query is position $`q_1 \in \{1, \ldots, 13\}`$;
- the $`j`$-th query is position\
  $`\displaystyle q_j(v_1, \ldots, v_{j-1}) \in \{1, \ldots, 13\} \setminus \{q_1, \ldots, q_{j-1}\},`$\
  where $`v_i`$ is the tile type seen at the $`i`$-th view, and the earlier positions $`q_i`$ are uniquely determined by the known rule;
- the $`j`$-th view yields $`v_j = E(H)_{q_j(v_1, \ldots, v_{j-1})}`$;
- at most $`k`$ queries are made, after which a pre-fixed decoding rule outputs a subset of $`T`$.

**Exactly $`k`$ views.** Early stopping may be allowed. For comparison, a protocol that stops early can be extended to exactly $`k`$ views by reading further unread positions and ignoring the results; this does not change the answer. Hence everything below is phrased with exactly $`k`$ views.

**Decoding.** Because each query position is a deterministic function of earlier observations, the complete history of query positions can be reconstructed from the ordered sequence of observed tile types $`(v_1, \ldots, v_k)`$. The final decoding rule can therefore be written as $`D_A : T^k \to \mathcal P(T)`$.

**The optimum of model A** is

```math
k_A = \min\bigl\{\, k \in \{0, \ldots, 13\} : \exists\ E,\ (q_j)_{j \le k},\ D_A \ \text{such that}\ \forall H \in \mathcal H,\ D_A(v_1, \ldots, v_k) = W(H) \,\bigr\}.
```

The quantifiers mean that **there is one uniform protocol under which every legal hand is decoded correctly**, not that a separate rule is negotiated for each hand.

## 5. Model B: pre-fixed-position viewing

**The positions.** Before seeing any tile face of the current hand, the two parties agree on $`k`$ distinct query positions

```math
I = (i_1, \ldots, i_k), \qquad i_j \in \{1, \ldots, 13\}, \quad i_a \ne i_b\ (a \ne b).
```

Bing may look only at these positions; the ordered observation is

```math
v = (E(H)_{i_1}, \ldots, E(H)_{i_k}).
```

Note that even if all $`k`$ tiles are turned over at once, **their faces and their positions remain visible**. The observation is therefore an ordered, position-labelled $`k`$-tuple, not an unordered multiset.

**Decoding.** A decoding function $`D_B : T^k \to \mathcal P(T)`$ is agreed in advance, with the requirement

```math
\forall H \in \mathcal H, \qquad D_B(E(H)_{i_1}, \ldots, E(H)_{i_k}) = W(H).
```

**The optimum of model B** is

```math
k_B = \min\bigl\{\, k \in \{0, \ldots, 13\} : \exists\ I, E, D_B \ \text{such that the condition above holds for all}\ H \in \mathcal H \,\bigr\}.
```

**Fixing $`I`$ without loss of generality.** Since the 13 positions can be uniformly relabelled in advance, one may take

```math
I = (1, 2, \ldots, k).
```

This convention means "look at the first $`k`$ tiles". It does not assume that Dai would otherwise lay the hand out in some natural mahjong order: **Dai may still arrange all 13 of the tiles actually held in any order.**

## 6. Theorem: under the constraints above, adaptive and fixed-position viewing have the same optimum

> **Theorem (equivalence of the two viewing protocols).** Suppose that:
> 1. Dai may arrange all 13 tiles arbitrarily;
> 2. the two parties share a deterministic protocol in advance;
> 3. the tile backs are identical and there is no side channel other than position;
> 4. Bing's query positions depend only on tile faces already turned over and on the publicly known rule.
>
> Then, for every $`k`$, model A is feasible if and only if model B is feasible. Hence
>
> ```math
> \boxed{k_A = k_B.}
> ```
>
> This conclusion **does not require knowing in advance whether the optimum is 3, 4 or any other integer**.

**Proof.**

1. **B ⇒ A.** In the adaptive model, Bing can simply ignore what has been seen and query the fixed positions of model B. Hence $`k_A \le k_B`$.
2. **A ⇒ B.** Take any model A protocol that guarantees success, with encoding function $`E_A`$, query rule $`q_1, \ldots, q_k`$ and decoding rule $`D_A`$.
   - **The observed sequence.** For each hand $`H`$, running the protocol yields a definite **ordered observation sequence** $`v(H) = (v_1(H), \ldots, v_k(H))`$.
   - **It is admissible.** Since model A only queries distinct positions, no tile type occurs in $`v(H)`$ more often than in $`H`$.
   - **A new encoding.** Dai can therefore switch to a new encoding $`E_B`$: place $`v_1(H), \ldots, v_k(H)`$ in order at the **fixed first $`k`$ positions**, and arrange the remaining $`13 - k`$ tiles arbitrarily after them. Then $`E_B(H) \in \operatorname{Perm}(H)`$, fully within the encoding constraints.
   - **Decoding.** Bing reads the first $`k`$ positions and obtains exactly the observation sequence $`v(H)`$ of model A. Applying $`D_A`$ directly outputs $`W(H)`$. Hence $`k_B \le k_A`$.
3. Combining both directions gives $`k_A = k_B`$. $`\square`$

**Intuition.** An adaptive protocol might have queried positions $`7, 2, 11, 5`$ in turn and obtained four ordered tile types. Dai knows the whole hand, the protocol and the resulting query path, so Dai can place these four tiles at positions $`1, 2, 3, 4`$ in **the same order of observation**. The position path itself carries no independent information to transmit, because it is fully determined by the tile types seen and the agreed rule.

**Significance.** The two forms may be kept as variants of the puzzle, but under the present assumptions they cannot give different minimum numbers of tiles. One may first solve the structurally simpler model B; its optimum then applies to model A as well.

## 7. A unified combinatorial form without the viewing process

For each hand $`H`$, define the set of all **ordered messages** of length $`k`$ that it can lay out:

```math
A_k(H) = \bigl\{\, (t_1, \ldots, t_k) \in T^k :\ \forall t \in T,\ \#\{\, j : t_j = t \,\} \le c_H(t) \,\bigr\}.
```

That is, a message may not use any tile beyond the hand's stock.

The common optimum of the two models can then be defined **without any reference to table positions** as

```math
\boxed{\displaystyle k^* = \min\Bigl\{\, k \in \{0, \ldots, 13\} : \exists f : \mathcal H \to T^k,\ \forall H\ f(H) \in A_k(H),\ \forall H, H'\ \bigl(f(H) = f(H') \Rightarrow W(H) = W(H')\bigr) \,\Bigr\}.}
```

Here $`f(H)`$ is the message that Dai encodes in the first $`k`$ tiles. One ordered message may be reused by different hands with **the same wait set**, but may not be used by hands with different wait sets.

Equivalently, let $`\mathcal W = \{\, W(H) : H \in \mathcal H \,\}`$ be the set of wait sets that actually occur. One seeks pairwise disjoint message sets $`(C_w)_{w \in \mathcal W}`$ such that

```math
\forall w \ne w',\ C_w \cap C_{w'} = \varnothing \quad\text{and}\quad \forall H \in \mathcal H,\ A_k(H) \cap C_{W(H)} \ne \varnothing.
```

This form directly gives a finite **zero-error coding / constraint satisfaction problem**, suitable for enumeration, constructive proof or Lean formalisation.

The basic bounds are

```math
1 \le k^* \le 13.
```

The upper bound holds because, after turning over all 13 tiles, the wait set can be computed directly. The lower bound holds because at least two different wait sets exist, so zero tiles are not enough.

## 8. A precise statement of "the optimum is four tiles"

The candidate proposition under study is

```math
\boxed{k^* = 4.}
```

To prove it, both of the following must be completed:

- **Feasibility (upper bound).** Give a four-tile encoding and decoding scheme valid for all $`H \in \mathcal H`$, or a reproducible program or formal certificate that fully verifies this, that is, $`k^* \le 4`$.
- **Optimality (lower bound).** Prove that no three-tile (or shorter) encoding scheme works for all $`H \in \mathcal H`$, that is, $`k^* \gt 3`$.

"Enumerating millions or tens of millions of hands of some kind" supports the corresponding proof only if three conditions all hold:
- it **covers all input classes and overlapping cases**;
- its rules agree completely with §2;
- it verifies the encoding-conflict condition and completeness.

One cannot assert, merely from someone else's description of their results, that both goals have been proved.

## 9. Further variants, different from the two main models (not studied here)

The following changes **alter the problem's definition** and may in principle change the optimum; they are not the two main models of this document.

1. **Viewing positions hidden from Dai, or chosen by an adversary.** If, after Dai has arranged the tiles, decoding must succeed whichever $`k`$ positions are turned over, this is not model B. In model B the fixed positions are **agreed jointly in advance** and Dai can exploit them; "every set of positions must succeed" adds a universal quantifier and is a stronger requirement.
2. **Simultaneous viewing with shuffled positions.** If Bing obtains only the **unordered multiset** of the $`k`$ tiles, without knowing which chosen position each came from, then the information carried by the arrangement is reduced; this differs from model B.
3. **Restricting Dai's arrangement.** For example, if Dai may only sort the hand in the customary mahjong order, or may only swap a few positions, then the equivalence proof of §6 no longer applies directly.
4. **Requiring the whole hand to be reconstructed.** Changing the goal from $`W(H)`$ to $`H`$ gives a different, stronger communication task, not studied here.

## 10. The formal problem statement adopted (concise version)

**Definition.** Let $`T`$ be the set of the 34 standard Japanese mahjong tile types, with at most four copies of each. Let $`\mathcal G`$ be the set of all legal 14-tile winning multisets formed by the standard four-melds-and-a-pair shape, seven distinct pairs, or thirteen orphans. For any 13-tile hand $`H`$, let

```math
W(H) = \{\, t \in T : c_H(t) < 4,\ H \uplus \{t\} \in \mathcal G \,\}
```

denote all valid waiting tile types, and let $`\mathcal H`$ be the set of all legal 13-tile hands with $`W(H) \ne \varnothing`$.

**Communication protocol.**
- The sender learns $`H`$, may only rearrange its 13 physical tiles, and places them all face down at 13 labelled fixed positions.
- The receiver does not know $`H`$ and knows only the jointly agreed rule. After viewing the tiles at no more than $`k`$ distinct positions, the receiver must report exactly the set $`W(H)`$.
- All other side channels are forbidden, and the same protocol must be correct for every $`H \in \mathcal H`$.

**To be determined.** The least integer $`k^*`$ in two settings:
- (A) the receiver may choose later positions adaptively, based on earlier views;
- (B) the receiver fixes all viewing positions before seeing any tile face.

**Under this model one can prove $`k_A = k_B = k^*`$**. It therefore suffices to find one common optimum, together with a construction and a proof of impossibility.

---

**Boundary of this document.** The mathematical objects, the rules and the equivalence of the two protocols are fixed here. The specific value of $`k^*`$ has not yet been found or verified. Any claim that "four tiles is the minimum" still requires a separate rigorous construction for the upper bound and proof of the lower bound.
