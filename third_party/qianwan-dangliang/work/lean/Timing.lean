import Mj.Upper
open Mj

def main : IO Unit := do
  let t0 ← IO.monoMsNow
  let a := structOk
  let t1 ← IO.monoMsNow
  let b := iBlocksAllCovered
  let t2 ← IO.monoMsNow
  let c := failuresAreReal
  let t3 ← IO.monoMsNow
  let d := iUnitsAllStrict
  let t4 ← IO.monoMsNow
  let e := iUnitsOkExcept
  let t5 ← IO.monoMsNow
  IO.println s!"structOk (a+b)            = {a}  [{t1 - t0} ms]"
  IO.println s!"iBlocksAllCovered (168817)= {b}  [{t2 - t1} ms]"
  IO.println s!"failuresAreReal (135)     = {c}  [{t3 - t2} ms]"
  IO.println s!"iUnitsAllStrict           = {d}  [{t4 - t3} ms]"
  IO.println s!"iUnitsOkExcept            = {e}  [{t5 - t4} ms]"
  IO.println s!"nIUnits={nIUnits} nIIUnits={nIIUnits} nIIStrictFailures={nIIStrictFailures}"
  IO.println s!"iUnitFailures.length={iUnitFailures.length} nUnitFailures={nUnitFailures} nFillVectors={nFillVectors}"
