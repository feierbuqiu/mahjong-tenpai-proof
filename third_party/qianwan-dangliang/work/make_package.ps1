# 打包「麻将翻牌猜听牌」两条证明路径的成果（路径 A: Python 证明链 / 路径 B: Lean 4 形式化）
# 用法: pwsh -NoProfile -File work\make_package.ps1 [-Out <zip路径>]
param([string]$Out = 'D:\DSH\MJ2\mahjong_tenpai_proof_package.zip')
$ErrorActionPreference = 'Stop'
$root = 'D:\DSH\MJ2'
$list = Join-Path $root 'work\_packagelist.txt'

$files = Get-ChildItem $root -Recurse -File | Where-Object {
  $rel = $_.FullName.Replace($root + '\', '')
  $skip = $false
  if ($rel -match '\\\.lake\\|\\__pycache__\\|\\.git\\') { $skip = $true }
  if ($rel -match '\.pkl$') { $skip = $true }
  # mathlib：只留配置，排除 6.7 GB 依赖缓存
  if ($rel -match '^lean-mathlib\\' -and $rel -notmatch 'lakefile|lake-manifest|lean-toolchain|README') { $skip = $true }
  # 中间搜索产物（保留 work/verify/plan_k4_FINAL.json 作为权威方案）
  if ($rel -match '^work\\strategy\\out\\replace_candidates\.json$') { $skip = $true }
  if ($rel -match '^work\\strategy\\out\\plan_k4_.*\.json$') { $skip = $true }
  if ($rel -match '^work\\recon\\plan_k4_.*\.json$') { $skip = $true }
  if ($rel -match '^work\\verify\\plan_k4_(?!FINAL).*\.json$') { $skip = $true }
  # 测量/临时残留与本包自身
  if ($rel -match '^lean\\mem_test\.lean$|^work\\lean_hand_input\.txt$') { $skip = $true }
  if ($rel -match '^work\\lean\\(peak|sum4_peak|conj_peak|l6total_rw|l6total_solo|l6total_v3|two_out|two_err)') { $skip = $true }
  if ($rel -match '^mahjong_tenpai_proof_package\.zip$|^work\\_packagelist\.txt$') { $skip = $true }
  -not $skip
}

$files | ForEach-Object { $_.FullName.Replace($root + '\', '').Replace('\', '/') } | Set-Content -Encoding ASCII $list
$tot = ($files | Measure-Object Length -Sum).Sum
Write-Output "文件数=$($files.Count)  未压缩体积=$([math]::Round($tot/1MB,2)) MB"

if (Test-Path $Out) { Remove-Item $Out -Force }
tar -a -cf $Out -C $root -T $list
if ($LASTEXITCODE -ne 0) { throw "tar 打包失败 exit=$LASTEXITCODE" }
$zip = Get-Item $Out
Write-Output "压缩包=$($zip.FullName)  大小=$([math]::Round($zip.Length/1MB,2)) MB"
$entries = (tar -tf $Out | Measure-Object -Line).Lines
Write-Output "归档条目数=$entries"
