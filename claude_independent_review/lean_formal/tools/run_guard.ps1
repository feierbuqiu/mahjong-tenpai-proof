param([string]$file, [int]$maxMB = 12000)
# run lean on one file; sample private bytes each second; kill above maxMB; log time / peaks / exit code
$env:LEAN_PATH = (Resolve-Path ".lake/build/lib/lean").Path
$lean = "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.35.0\bin\lean.exe"
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath $lean -ArgumentList $file -NoNewWindow -PassThru -RedirectStandardOutput "$file.out" -RedirectStandardError "$file.err"
$peakPriv = 0; $peakWS = 0; $killed = $false
while (-not $p.HasExited) {
  try { $p.Refresh(); if ($p.PrivateMemorySize64 -gt $peakPriv) { $peakPriv = $p.PrivateMemorySize64 }; if ($p.WorkingSet64 -gt $peakWS) { $peakWS = $p.WorkingSet64 } } catch {}
  if ($peakPriv -gt $maxMB * 1MB) { Stop-Process -Id $p.Id -Force; $killed = $true; break }
  Start-Sleep -Milliseconds 1000
}
$p.WaitForExit()
$sw.Stop()
"{0} exit={1} killed={2} sec={3:N1} peakPrivMB={4:N0} peakWsMB={5:N0}" -f $file, $p.ExitCode, $killed, $sw.Elapsed.TotalSeconds, ($peakPriv/1MB), ($peakWS/1MB) | Out-File -Append -Encoding utf8 guard_times.txt
