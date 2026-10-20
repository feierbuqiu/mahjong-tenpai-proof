param([string[]]$Files)
foreach ($f in $Files) {
  $t0 = Get-Date
  $p = Start-Process -FilePath "lake" -ArgumentList "env", "lean", $f -WorkingDirectory "D:\DSH\MJ2\lean" -NoNewWindow -PassThru `
       -RedirectStandardOutput "D:\DSH\MJ2\work\lean\two_out.txt" -RedirectStandardError "D:\DSH\MJ2\work\lean\two_err.txt"
  $peak = 0
  while (-not $p.HasExited) {
    Start-Sleep -Milliseconds 700
    foreach ($k in (Get-Process -Name lean -ErrorAction SilentlyContinue)) { if ($k.WorkingSet64/1MB -gt $peak) { $peak = [int]($k.WorkingSet64/1MB) } }
  }
  $p.WaitForExit()
  Write-Output "file=$f exit=$($p.ExitCode) elapsed=$([int]((Get-Date)-$t0).TotalSeconds)s peakMB=$peak"
}
