param([string]$File = 'mem_test.lean')
$t0 = Get-Date
$p = Start-Process -FilePath lean -ArgumentList $File -PassThru -NoNewWindow -RedirectStandardOutput lean/mem_test.out -RedirectStandardError lean/mem_test.err -WorkingDirectory lean
$peak = 0
while (-not $p.HasExited) { try { $p.Refresh(); if ($p.WorkingSet64 -gt $peak) { $peak = $p.WorkingSet64 } } catch {}; Start-Sleep -Milliseconds 300 }
$p.WaitForExit()
'file=' + $File
'seconds=' + [math]::Round(((Get-Date)-$t0).TotalSeconds,1)
'exit=' + $p.ExitCode
'peak_MB=' + [math]::Round($peak/1MB,1)
Get-Content lean/mem_test.out -TotalCount 4 | Out-String