from math import comb
tot = comb(21,13)
a1 = 9*comb(16,8)
a2 = comb(9,2)*comb(11,3)
a3 = comb(9,3)*comb(8,-2) if False else 0
print("C(21,13)=",tot," -9*C(16,8)=",a1," +C(9,2)*C(11,3)=",a2, " => ", tot-a1+a2-a3)
