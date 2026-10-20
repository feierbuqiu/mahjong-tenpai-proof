# L6 全量内核验证：16 个批次模块，4 路并发（内存预算：4 x ~3GB << 32GB）
$ErrorActionPreference = "Continue"
$LeanDir = "D:\DSH\MJ2\lean"
$LogDir  = "D:\DSH\MJ2\work\lean"
$log     = Join-Path $LogDir "l6_build.log"
Set-Content $log "start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$mods = 0..15 | ForEach-Object { "Mj.L6B{0:D2}" -f $_ }

for ($i = 0; $i -lt 16; $i += 4) {
  $wave = $mods[$i..([math]::Min($i + 3, 15))]
  Add-Content $log "=== wave starting $($wave -join ',') at $(Get-Date -Format HH:mm:ss)"
  $procs = @()
  foreach ($m in $wave) {
    $out = Join-Path $LogDir "out_$m.txt"
    $err = Join-Path $LogDir "out_$m.err.txt"
    $p = Start-Process -FilePath "lake" -ArgumentList "build", $m -WorkingDirectory $LeanDir `
         -NoNewWindow -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    $procs += [pscustomobject]@{ m = $m; p = $p; out = $out }
  }
  foreach ($x in $procs) {
    $x.p.WaitForExit()
    $tail = (Get-Content $x.out -Tail 2 -ErrorAction SilentlyContinue) -join " | "
    $etxt = (Get-Content ($x.out -replace '\.txt$', '.err.txt') -Tail 2 -ErrorAction SilentlyContinue) -join " | "
    Add-Content $log "$($x.m) exit=$($x.p.ExitCode) at $(Get-Date -Format HH:mm:ss) :: $tail $etxt"
  }
}
Add-Content $log "=== all waves done at $(Get-Date -Format HH:mm:ss)"
