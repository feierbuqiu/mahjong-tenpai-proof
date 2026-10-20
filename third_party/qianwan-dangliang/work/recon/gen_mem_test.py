import sys
n = int(sys.argv[1])
chunk = 40
lines = ['set_option maxHeartbeats 0', '', 'def big : List Nat :=']
for i in range(0, n, chunk):
    body = ','.join(str(x) for x in range(i, min(i+chunk, n)))
    lines.append('  [' + body + '] ++')
lines[-1] = lines[-1].rstrip(' +')
lines.append('')
lines.append('#eval big.length')
open('lean/mem_test.lean','w',encoding='utf-8').write(chr(10).join(lines))
print('generated', n, 'literals; file MB', round(len(chr(10).join(lines))/1e6,2))
