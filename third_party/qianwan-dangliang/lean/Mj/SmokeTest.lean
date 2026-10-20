-- 最小可用性验证：编译链 / decide / native_decide / 有限枚举
namespace Mj

theorem two_plus_two : (2 : Nat) + 2 = 4 := by decide

/-- Fin 34 的枚举（牌张编号 0..33） -/
def allTiles : List (Fin 34) := List.finRange 34

theorem allTiles_length : allTiles.length = 34 := by native_decide

/-- 清一色 9 张牌的 2-码数量 = 9^2 = 81 -/
theorem flush_codes_k2 : (allTiles.take 9).length ^ 2 = 81 := by native_decide

end Mj
