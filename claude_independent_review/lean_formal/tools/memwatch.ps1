param([string]$out = "memwatch.txt", [int]$intervalSec = 5)
# Samples all lean.exe processes until lake exits; logs total / max-single working set and per-process peaks.
$peakTotal = 0; $peakSingle = 0; $peaks = @{}
$start = Get-Date
"start $start" | Out-File -Encoding utf8 $out
while ($true) {
  $ps = @(Get-CimInstance Win32_Process -Filter "Name='lean.exe'")
  $lake = @(Get-Process lake -ErrorAction SilentlyContinue)
  $tot = 0
  foreach ($p in $ps) {
    $ws = [int64]$p.WorkingSetSize; $tot += $ws
    if ($ws -gt $peakSingle) { $peakSingle = $ws }
    $m = if ($p.CommandLine -match 'Tenpai[\\/]([^"]+?)\.lean') { $Matches[1] } else { "?" }
    if (-not $peaks.ContainsKey($m) -or $peaks[$m] -lt $ws) { $peaks[$m] = $ws }
  }
  if ($tot -gt $peakTotal) { $peakTotal = $tot }
  $el = [int]((Get-Date) - $start).TotalSeconds
  "{0,6}s procs={1} totalMB={2:N0}" -f $el, $ps.Count, ($tot / 1MB) | Out-File -Append -Encoding utf8 $out
  if ($lake.Count -eq 0 -and $ps.Count -eq 0) { break }
  Start-Sleep -Seconds $intervalSec
}
"end $(Get-Date) peakTotalMB={0:N0} peakSingleMB={1:N0}" -f ($peakTotal / 1MB), ($peakSingle / 1MB) | Out-File -Append -Encoding utf8 $out
$peaks.GetEnumerator() | Sort-Object Name | ForEach-Object { "peak {0} {1:N0}MB" -f $_.Name, ($_.Value / 1MB) } | Out-File -Append -Encoding utf8 $out
