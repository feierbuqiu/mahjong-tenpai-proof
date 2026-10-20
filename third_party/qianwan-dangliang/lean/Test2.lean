import Mj.Basic
open Mj
def mk (pairs : List (Nat × Nat)) : Hand :=
  ⟨(pairs.foldl (fun a p => a.set! p.1 p.2) (List.replicate 34 0).toArray)⟩
def kokushi13 : Hand := ⟨(kokushiIdx.foldl (fun a i => a.set! i 1) (List.replicate 34 0).toArray)⟩
#eval (waits kokushi13).map (fun t => t.val)   -- 应为 13 个幺九
-- 交叉测试：从前 300 个单花色手牌导出 (计数向量, 听牌) 供与 Python 对拍
#eval (flushHands.take 300).map (fun H => (H.v.toList, (waits H).map (fun t => t.val)))
