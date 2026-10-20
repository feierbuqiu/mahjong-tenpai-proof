# L7 HANDOFF —— 去掉 Mj.Upper 的 iiUnitsComplete 假设

> owner: enum-core ｜ 写作用域：`lean/Mj/Upper.lean`、`lean/Mj/L6Upper.lean`、`work/lean/L7_HANDOFF.md`
> 依赖（Lead/analyst-lower 所有，未改）：`Mj/L6Index.lean`、`Mj/L6B00..L6B15.lean`、`Mj/L6Total.lean`、`Mj/L6Bridge.lean`

## 1. 改动内容

| 文件 | 改动 |
|---|---|
| `lean/Mj/L6Upper.lean`（新增） | 定义 `iiUnitsCovered`：由 `totalIdx`（= 16 批 `batchAt` 之和，(块数, 失败块数, 单元数, 失败单元数)）给出 —— 覆盖全部 309,144 块、失败块 0、单元 5,402,697、失败单元 0。`iiUnitsCovered_true` 用 `rw [l6TotalIdx_eq]` 内核证明（**不重新求值**）。另附接口引理 `iiBlockCovered_of_zero`。 |
| `lean/Mj/Upper.lean` | **删除** `axiom iiUnitsComplete` 与 `axiom iiUnitsComplete_proof`；新增 `import Mj.L6Upper`；`checkPlan_true` 改为 `checkPlanComputable = true ∧ iiUnitsCovered`；`upper_k4` 改为只依赖 `structOk_true / iBlocksAllCovered_true / failuresAreReal_true / iUnitsAllStrict_false / iiUnitsCovered_true`；`#print axioms` 行同步更新。 |

II 型检查语义不变（Mj.Upper2 的块级语义：strict 单码通道 + 多码/DFS 通道、DFS 用全码），
只是把「结论」从 axiom 换成 Lead 的 16 批 native_decide 拼接定理。

## 2. #print axioms 对比（验收项）

**改动前**（tag task-14 时的构建日志 `work/lean/build_upper.log`）：
```
info: Mj/Upper.lean:209:0: 'Mj.checkPlan_true' depends on axioms: [propext,
 iiUnitsComplete,
 iiUnitsComplete_proof,
 failuresAreReal_true._native.native_decide.ax_1_1,
 iBlocksAllCovered_true._native.native_decide.ax_1_1,
 structOk_true._native.native_decide.ax_1_1]
```

**改动后**：见本文件 §4 的实测输出（`lake build Mj.Upper` 一次通过，375 s）。
预期：只剩 `propext` 与各 `*_native.native_decide.ax_1_1`（native_decide 的可信基），
**不再出现 `iiUnitsComplete` / `iiUnitsComplete_proof`**。

## 3. 状态

- [x] Upper.lean 已删假设、已改为引用 `Mj.L6Upper`（文本层面完成）
- [x] L6Upper.lean 已写好（`iiUnitsCovered` + `iiUnitsCovered_true`）
- [x] 16 个批次模块 L6B00..L6B15 的 .olean 已由 Lead 的 wave 产出
- [x] `lake build Mj.Upper` **绿**（Lead 解冻后一次通过）：`Build completed successfully (25 jobs)`，375 s。
      （此前那次 >18 min 无进度是我在等 Lake 构建锁时主动取消的；根因是机器的 lean 进程内存踩踏，
       Lead 定位为 batchAt 重写触发 chunkBlocks 反复求值导致 OOM，解法是 b00..b15 别名。）
- [x] **参数化版本已单独验证**（`work/lean/L6Upper_check.lean`，只 import 已建好的 `Mj.L6Index`，1 个 lean 进程）：
      `iiUnitsCovered_true_of (h : totalIdx = (309144, 0, 5402697, 0))` 与 `iiBlockCovered_of_zero` 均编译通过
      ⇒ 谓词、证明骨架、接口引理无语法/类型问题；只差把 `h` 换成 `l6TotalIdx_eq`（同一形状的 `rw`）。
- [x] 改动后的 `#print axioms` 已采集（见 §4）

## 4. 改动后的 #print axioms（实测，2026-09-18）

```
info: Mj/Upper.lean:200:0: 'Mj.checkPlan_true' depends on axioms: [propext,
 Quot.sound,
 failuresAreReal_true._native.native_decide.ax_1_1,
 iBlocksAllCovered_true._native.native_decide.ax_1_1,
 l6_batch00_eq._native.native_decide.ax_1_1,
 ... （l6_batch01..l6_batch14 各一条，共 16 条） ...
 l6_batch15_eq._native.native_decide.ax_1_1,
 structOk_true._native.native_decide.ax_1_1]
info: Mj/Upper.lean:201:0: 'Mj.upper_k4' depends on axioms: [propext, Quot.sound,
 failuresAreReal_true._native…, iBlocksAllCovered_true._native…, iUnitsAllStrict_false._native…,
 l6_batch00..15_eq._native…]
info: Mj/Upper.lean:202:0: 'Mj.iBlocksAllCovered_true' depends on axioms: [propext,
 iBlocksAllCovered_true._native.native_decide.ax_1_1]
info: Mj/Upper.lean:203:0: 'Mj.structOk_true' depends on axioms: [structOk_true._native.native_decide.ax_1_1]
```

**结论**：改动后 `checkPlan_true` 的依赖只有
`propext`、`Quot.sound`、三个本文件的 native_decide 可信基、以及 **16 条 l6_batchNN_eq 的 native_decide 可信基**；
**`iiUnitsComplete` / `iiUnitsComplete_proof` 已彻底消失，也没有 `sorryAx`**。
即：5,402,697 个 II 型单元的块级覆盖现在是**内核已验证**（经 Mj.L6Total.totalIdx_eq），不再是 assumption。

### 比较（before → after）

| | axioms |
|---|---|
| before | `[propext, iiUnitsComplete, iiUnitsComplete_proof, failuresAreReal_true._native…, iBlocksAllCovered_true._native…, structOk_true._native…]` |
| after | `[propext, Quot.sound, failuresAreReal_true._native…, iBlocksAllCovered_true._native…, l6_batch00..15_eq._native… (16 条), structOk_true._native…]` |

剩余 assumption：**无**（Mj/Upper.lean 里已无任何 `axiom`；全项目的公理只剩 Lean 内核的 `propext`/`Quot.sound` 与 native_decide 的 `Lean.ofReduceBool` 类可信基）。

## 5. 复现命令

    cd lean
    lake build Mj.L6Total      # Lead 负责（16 批 native_decide，4 路并发 ~20 min）
    lake build Mj.Upper        # 本任务验收：全绿 + #print axioms 无 iiUnitsComplete

---

## 附录 A：L7 删除/改名定义的原样文本（可追溯记录；无 git 仓库，以此为准）

### A.1 删除的两个定义（原先位于 `import Mj.L6Upper` 之后、`catOff` 之前）

```lean
/-- 牌 t 的类别 -/
def tileCat (t : Nat) : Nat := if t < 27 then t / 9 else 3

/-- 牌 t 在类别内的位置 -/
def tilePos (t : Nat) : Nat := if t < 27 then t % 9 else t - 27
```

删除原因：`import Mj.L6Upper` 会把 `Mj.Upper2` 带入同一 namespace，其中已有**同名同体**的
`tileCat` / `tilePos`（Upper2 第 41–42 行），触发 "has already been declared"。
这两个定义在 Upper.lean 内**除自身声明外没有任何引用**（删除是惰性改动）。

### A.2 `reqOk` -> `reqOkOne` 改名（两处，原样文本）

```lean
-- 改名前的定义（原文）
def reqOk (r : Nat × Nat) (h : Nat) : Bool := decide (r.2 ≤ (h >>> r.1) &&& 7)

-- 改名前的唯一使用点（原文，位于 codeInHand 内）
def codeInHand (cr : List (Nat × Nat)) (h : Nat) : Bool := cr.all (fun r => reqOk r h)
```

```lean
-- 改名后（现状）
def reqOkOne (r : Nat × Nat) (h : Nat) : Bool := decide (r.2 ≤ (h >>> r.1) &&& 7)
def codeInHand (cr : List (Nat × Nat)) (h : Nat) : Bool := cr.all (fun r => reqOkOne r h)
```

改名原因：`Mj.Upper2` 已有 `reqOk (reqs : List (Nat × Nat)) (X : List Nat) : Bool`（类型不同，
本就不可能与打包版混用），同名会触发 "has already been declared"。
改动仅限标识符，函数体与调用点逐字未变。

### A.3 本次 L7 对 lean/Mj/Upper.lean 的**全部**改动（共 5 类）

1. 删除 `axiom iiUnitsComplete` 与 `axiom iiUnitsComplete_proof`（连同其上方的旧注释块）；
2. 新增 `import Mj.L6Upper`（文件头注释同步改写）；
3. `checkPlan_true` / `upper_k4` 结论重排：
   - `checkPlan_true : checkPlanComputable = true ∧ iiUnitsCovered`
   - `upper_k4 : structOk = true ∧ iBlocksAllCovered = true ∧ failuresAreReal = true ∧ iUnitsAllStrict = false ∧ iiUnitsCovered`
   - `#print axioms` 行按新结论调整；
4. 删除 A.1 的两个同名定义、把 A.2 的 `reqOk` 改名 `reqOkOne`；
5. 补上替换注释块时漏掉的 `-/` 结束符。

**未改动**任何喂给 `iBlocksAllCovered` / `structOk` / `failuresAreReal` 的定义体：
`blockCovAux` / `unitBlockCovered` / `unitHand` / `codeReq` / `iUnitData` 的用法 / `codesLen4` /
`codesUnique` / `classesNonEmpty` / `iUnitsAllStrict` / `iUnitsOkExcept` / `checkPlanComputable`
逐字未动（改动只有 A.1/A.2 的「消歧义」与上述 1/2/3/5 的注释与结论重排）。

