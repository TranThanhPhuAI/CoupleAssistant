<#
Đưa web lên Vercel MIỄN PHÍ, không cần tên miền: mở backend qua Cloudflare Quick Tunnel (địa chỉ *.trycloudflare.com)
rồi đóng gói giao diện với địa chỉ đó và đưa lên Vercel (project couple-assistant).

  .\tools\vercel_quick.ps1

Cần: server đang chạy (python run.py web, cổng 8000) và đã đăng nhập Vercel (npx vercel login).
Lưu ý: địa chỉ trycloudflare ĐỔI mỗi lần chạy lại -> mỗi lần bật lại máy thì chạy lại lệnh này (khoảng 1 phút).
Đóng đường hầm: tắt tiến trình cloudflared (Task Manager) hoặc khởi động lại máy.
#>
param([int]$Port = 8000)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

try { Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 5 | Out-Null }
catch { throw "Server chưa chạy ở cổng $Port. Mở cửa sổ khác: .venv\Scripts\activate ; python run.py web" }

$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
foreach ($p in @("${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe", "$env:ProgramFiles\cloudflared\cloudflared.exe")) { if (-not $cf -and (Test-Path $p)) { $cf = $p } }
if (-not $cf) {
    Write-Host "Cài cloudflared (Windows có thể hỏi quyền)..."
    winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements | Out-Null
    $cf = "${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe"
    if (-not (Test-Path $cf)) { throw "Chưa cài được cloudflared. Mở PowerShell mới rồi chạy lại." }
}

$log = Join-Path $env:TEMP "couple_assistant_quick_tunnel.log"
Remove-Item $log -ErrorAction SilentlyContinue
Write-Host "Mở đường hầm tạm tới http://127.0.0.1:$Port ..."
Start-Process $cf -ArgumentList "tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:$Port" -RedirectStandardError $log -WindowStyle Hidden | Out-Null
$url = $null
for ($i = 0; $i -lt 60 -and -not $url; $i++) {
    Start-Sleep 1
    if (Test-Path $log) { $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1; if ($m) { $url = $m.Matches[0].Value } }
}
if (-not $url) { throw "Không lấy được địa chỉ trycloudflare (xem log: $log)" }
Write-Host "Backend: $url  (đợi DNS sẵn sàng...)"
for ($i = 0; $i -lt 30; $i++) { try { Invoke-RestMethod "$url/api/health" -TimeoutSec 10 | Out-Null; break } catch { Start-Sleep 3 } }

& $Py (Join-Path $Root "tools\vercel_build.py") $url
if ($LASTEXITCODE -ne 0) { throw "Đóng gói lỗi" }
Push-Location (Join-Path $Root "dist\vercel")
try {
    if (-not (Test-Path ".vercel")) { npx --yes vercel link --yes --project couple-assistant }
    npx --yes vercel deploy --prod --yes
} finally { Pop-Location }
Write-Host "`nXong: https://couple-assistant.vercel.app  (backend tạm: $url)"
Write-Host "Giữ máy bật và server chạy. Bật lại máy thì chạy lại: .\tools\vercel_quick.ps1"
