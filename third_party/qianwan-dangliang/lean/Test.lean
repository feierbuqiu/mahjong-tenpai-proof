import Mj.Basic
open Mj

-- 构造：计数数组
def mk (pairs : List (Nat × Nat)) : Hand :=
  ⟨(pairs.foldl (fun a p => a.set! p.1 p.2) (List.replicate 34 0).toArray)⟩

-- 单花色 13 张手牌总数（应为 93600）
#eval flushHands.length

-- 国士 13 面手牌：13 种幺九各 1 张；加任一张即和牌 ⇒ 13 面听
def kokushi13 : Hand := ⟨(kokushiIdx.foldl (fun a i => a.set! i 1) (List.replicate 34 0).toArray)⟩
#eval (waits kokushi13).length
#eval (kokushi13.total = 13)

-- 例：123m456m789m123p4p（13 张）
def h1 : Hand := mk [(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1),(10,1),(11,1),(12,1)]
#eval (waits h1).map (fun t => t.val)
#eval h1.total

-- 例：123m456m789m 1p1p 2p（13 张，听 2p? 或 1p?）
def h2 : Hand := mk [(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,2),(10,1)]
#eval (waits h2).map (fun t => t.val)
#eval h2.total

-- 严格七对子：6 对 + 1 单（听那张单牌）
def h3 : Hand := mk [(0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(9,1)]
#eval (waits h3).map (fun t => t.val)
#eval h3.total

-- 反例：4 张同牌不算两对（1111m + 5 对 + 单张 = 13 张）
def h4 : Hand := mk [(0,4),(1,2),(2,2),(3,2),(4,2),(5,2),(9,1)]
#eval (waits h4).map (fun t => t.val)

-- 和牌判定直测
def win1 : Hand := mk [(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1),(10,1),(11,1),(12,2)]
#eval isWin win1
#eval isWin kokushi13.add ⟨12, by decide⟩
