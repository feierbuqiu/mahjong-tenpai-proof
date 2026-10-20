# LEAN_L2 — task-11 验收记录（子宇宙预算引理，Mj/Lemma.lean）

验证者: verifier（T5/T6）。完成时间: 本轮。

## 1. 结论：通过，但有**两处题面语句修正**（均已用 Lean 反例机器验证）

产物:
- `lean/Mj/Lemma.lean`（sha256 840fea20f62de0b2…，293 行，子代理编写，verifier 独立复核 + 补 1 条桥引理）
- `lean/Mj.lean`：**verifier 加了 1 行** `import Mj.Lemma`（原来 `lake build` 默认目标不含 Mj.Lemma，加上后整库 6 jobs 构建才真正覆盖本文件）
- `lean/Counterexample.lean`：verifier 的反例文件（两处语句修正的机器证据）
- `work/verify/check_lean_lemma.py`：静态验收（禁用词 / 语句形状 / 冻结文件哈希）

## 2. 已证明（签名以文件为准）

```
def seqU (U : List Tile) : Nat → List (List Tile) | 0 => [[]] | k+1 => U.flatMap (fun t => (seqU U k).map (fun c => t :: c))
def codesU (U : List Tile) (k : Nat) : List (List Tile) := seqU U k
theorem mem_codesU        : c ∈ codesU U k ↔ c.length = k ∧ ∀ t, t ∈ c → t ∈ U
theorem codesU_nodup      (hU : U.Nodup) : ∀ k, (codesU U k).Nodup
theorem codesU_length     (U : List Tile) (k : Nat) : (codesU U k).length = U.length ^ k
theorem budget {k} {U} (hU : U.Nodup) (cls) (hcls : cls.Nodup) (hlen) (hsub) (hdisj)
    (hSnodup : ∀ S, S ∈ cls → S.Nodup) : (cls.map List.length).sum ≤ U.length ^ k
theorem classes_le_pow ... (hne : ∀ S, S ∈ cls → S ≠ []) : cls.length ≤ U.length ^ k
theorem no_common_code_two {k} {U} {Hs} (hHsne : Hs ≠ []) (S) (hS : ∀ c, c ∈ S → c.length = k ∧ ∀ t, t ∈ c → t ∈ U)
    (hcover : ∀ H, H ∈ Hs → ∃ c, c ∈ S ∧ c ∈ H)
    (hno : ∀ c, c.length = k → (∀ t, t ∈ c → t ∈ U) → ∃ H, H ∈ Hs ∧ c ∉ H) : 2 ≤ S.length
theorem contains_eq_true_iff (code) (H) : contains code H = true ↔ ∀ t, code.count t ≤ H.get t   -- 桥引理(Bool/Prop)
```

## 3. 两处修正与反例证据（`lake env lean Counterexample.lean` exit 0）

1. **budget 原语句缺 hcls / hSnodup**（lead 版）：
   - `U=[t0], k=1, cls=[[[t0],[t0]]]`：hU/hlen/hsub ✓、hdisj 真空 ✓，但 sum=2 > 1^1=1 ⇒ 反例成立；
   - `cls=[[[t0]],[[t0]]]`（重复类）同样 2 > 1。
   - 应用语义里 S_C 是**集合**、类是**互异**的，故这两条假设本就是隐含前提。
2. **推论 ② 原语句缺 hS**：`k=0, U=[t0], Hs=[[[t0]]], S=[[t0]]`：hHsne/hcover/hno 全 ✓ 但 `S.length = 1`，结论 2 ≤ 1 为假（`hno` 只作用于"长度 k 且元素属于 U"的码，原语句没有任何假设保证 S 的元素是这种码）。

## 4. 验收证据（本轮实测）

    cd D:/DSH/MJ2/lean
    lake build            -> Build completed successfully (6 jobs)   # 含 [4/6] Built Mj.Lemma
    lake build Mj.Lemma   -> Build completed successfully (3 jobs)
    lake env lean Mj/Lemma.lean  -> 0 error / 0 warning
    #print axioms Mj.budget            -> [propext, Classical.choice, Quot.sound]
    #print axioms Mj.classes_le_pow    -> [propext, Classical.choice, Quot.sound]
    #print axioms Mj.no_common_code_two-> [propext, Quot.sound]
    #print axioms Mj.contains_eq_true_iff -> [propext, Quot.sound]
    python -u work/verify/check_lean_lemma.py   -> 禁用词: 无；定理/假设/结论形状齐全

无 `axiom` / `sorry` / `admit` / `native_decide`（静态扫描 + 上述 #print 双重确认）。

## 5. 共享写域注意事项

- `lean/Mj/Basic.lean` 未被改动（sha256 5fd551611a62e742…，接口稳定；Lemma 只依赖它）。
- `lean/Mj.lean`：verifier 加 `import Mj.Lemma`（1 行，集成所需）。
- `lean/Mj/Disproof.lean` 在本轮内**由其他队友改动**（非 verifier）；整库构建在当前状态下仍全绿（6 jobs）。
- 工具链: leanprover/lean4:v4.33.1；仅 core/Std。
