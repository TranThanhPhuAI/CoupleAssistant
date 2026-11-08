<#
Triển khai Couple Assistant trên máy nhà (Windows).

  .\tools\trien_khai.ps1                                  xem trạng thái các tác vụ
  .\tools\trien_khai.ps1 -Tunnel hen.tenmien.com          tạo Cloudflare Tunnel (mở trình duyệt đăng nhập 1 lần; không cần admin)
  .\tools\trien_khai.ps1 -CaiLich [-CPU]                  cài lịch chạy ngầm, CẦN "Run as administrator"
  .\tools\trien_khai.ps1 -GoLich                          gỡ toàn bộ lịch

Lịch (thư mục \CoupleAssistant\ trong Task Scheduler), log ở data\logs\:
  Web      khi bật máy   python run.py web            (tự chạy lại nếu dừng)
  Ollama   khi bật máy   ollama serve                 (nếu tìm thấy ollama.exe)
  Tunnel   khi bật máy   cloudflared tunnel run       (nếu đã chạy -Tunnel)
  SaoLuu   02:00 hằng ngày        python run.py saoluu
  NhapMoi  02:30 hằng ngày        python run.py nhap --tat-ca   (đợt mới trong data\staging\)
  TinhLai  03:00 Chủ nhật         python run.py tinhlai
Server tự nạp lại dữ liệu sau khi nhập / tính lại — không cần khởi động lại.
#>
param(
    [string]$Tunnel,
    [switch]$CaiLich,
    [switch]$GoLich,
    [switch]$CPU   # model embedding chạy CPU, nhường GPU cho game
)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$Logs = Join-Path $Root "data\logs"
$Folder = "\CoupleAssistant\"
$TunnelName = "couple-assistant"
$CfDir = Join-Path $env:USERPROFILE ".cloudflared"
$CfConfig = Join-Path $CfDir "config.yml"

function Assert-Admin {
    $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Cần mở PowerShell bằng 'Run as administrator'."
    }
}

function Find-Cloudflared {
    $c = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    foreach ($p in @("${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe", "$env:ProgramFiles\cloudflared\cloudflared.exe")) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Find-Ollama {
    $c = Get-Command ollama -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    foreach ($p in @("E:\Ollama\app\ollama.exe", "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe")) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

# ---------------- Cloudflare Tunnel ----------------
function Initialize-Tunnel([string]$HostName) {
    if ($HostName -notmatch '^[a-z0-9-]+(\.[a-z0-9-]+)+$') { throw "Tên miền không hợp lệ: $HostName" }
    $cf = Find-Cloudflared
    if (-not $cf) {
        Write-Host "Cài cloudflared bằng winget..."
        winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
        $cf = Find-Cloudflared
        if (-not $cf) { throw "Chưa cài được cloudflared. Mở PowerShell mới rồi chạy lại." }
    }
    if (-not (Test-Path (Join-Path $CfDir "cert.pem"))) {
        Write-Host "Trình duyệt sẽ mở: đăng nhập Cloudflare và chọn tên miền của bạn."
        & $cf tunnel login
        if ($LASTEXITCODE -ne 0) { throw "Đăng nhập Cloudflare thất bại." }
    }
    $list = & $cf tunnel list --output json | ConvertFrom-Json
    $t = $list | Where-Object { $_.name -eq $TunnelName } | Select-Object -First 1
    if (-not $t) {
        & $cf tunnel create $TunnelName
        if ($LASTEXITCODE -ne 0) { throw "Không tạo được tunnel." }
        $t = (& $cf tunnel list --output json | ConvertFrom-Json) | Where-Object { $_.name -eq $TunnelName } | Select-Object -First 1
    }
    $cred = Join-Path $CfDir "$($t.id).json"
    if (-not (Test-Path $cred)) { throw "Thiếu file khóa tunnel $cred (tunnel tạo ở máy khác?). Xóa tunnel trên dashboard rồi chạy lại." }
    # chỉ chuyển tiếp đúng tên miền này tới server nội bộ; mọi thứ khác trả 404
    @"
tunnel: $($t.id)
credentials-file: $cred
ingress:
  - hostname: $HostName
    service: http://127.0.0.1:8000
  - service: http_status:404
"@ | Set-Content -Path $CfConfig -Encoding ascii
    & $cf tunnel route dns $TunnelName $HostName
    Write-Host "`nTunnel '$TunnelName' -> https://$HostName  (cấu hình: $CfConfig)"
    Write-Host "Tiếp theo: bật Cloudflare Access cho tên miền này (xem docs\TRIEN_KHAI.md, bước 3)."
}

# ---------------- Lịch tự động ----------------
function Add-Task([string]$Name, [string]$Command, $Trigger, [switch]$KeepAlive) {
    # cmd /c để ghi log; S4U = chạy ngầm bằng tài khoản này, không cửa sổ, không cần lưu mật khẩu
    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/s /c `"$Command`"" -WorkingDirectory $Root
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited
    $set = @{ AllowStartIfOnBatteries = $true; DontStopIfGoingOnBatteries = $true; StartWhenAvailable = $true;
              MultipleInstances = "IgnoreNew" }
    if ($KeepAlive) {
        $set.ExecutionTimeLimit = [TimeSpan]::Zero
        $set.RestartCount = 999
        $set.RestartInterval = New-TimeSpan -Minutes 1
    } else {
        $set.ExecutionTimeLimit = New-TimeSpan -Hours 3
    }
    $settings = New-ScheduledTaskSettingsSet @set
    Register-ScheduledTask -TaskPath $Folder -TaskName $Name -Action $action -Trigger $Trigger `
        -Principal $principal -Settings $settings -Force | Out-Null
    Write-Host ("  {0,-8} {1}" -f $Name, $Command)
}

function Install-Schedule {
    if (-not (Test-Path $Py)) { throw "Không thấy $Py. Cài môi trường Python theo README trước." }
    New-Item -ItemType Directory -Force $Logs | Out-Null
    $envs = "set PYTHONIOENCODING=utf-8&& "
    if ($CPU) { $envs += "set EMBED_DEVICE=cpu&& " }
    $run = "$envs`"$Py`" run.py"
    $boot = New-ScheduledTaskTrigger -AtStartup
    Write-Host "Cài lịch vào Task Scheduler $Folder"
    Add-Task "Web" "$run web >> `"$Logs\web.log`" 2>&1" $boot -KeepAlive
    $ol = Find-Ollama
    if ($ol) {
        $models = [Environment]::GetEnvironmentVariable("OLLAMA_MODELS", "User")
        $pre = if ($models) { "set OLLAMA_MODELS=$models&& " } else { "" }
        Add-Task "Ollama" "$pre`"$ol`" serve >> `"$Logs\ollama.log`" 2>&1" $boot -KeepAlive
    } else { Write-Host "  (bỏ qua Ollama: không tìm thấy ollama.exe — sẽ dùng Claude Haiku nếu có ANTHROPIC_API_KEY)" }
    $cf = Find-Cloudflared
    if ($cf -and (Test-Path $CfConfig)) {
        Add-Task "Tunnel" "`"$cf`" --config `"$CfConfig`" tunnel run $TunnelName >> `"$Logs\tunnel.log`" 2>&1" $boot -KeepAlive
    } else { Write-Host "  (bỏ qua Tunnel: chưa chạy -Tunnel <tên miền>)" }
    Add-Task "SaoLuu"  "$run saoluu >> `"$Logs\lich.log`" 2>&1" (New-ScheduledTaskTrigger -Daily -At 2:00am)
    Add-Task "NhapMoi" "$run nhap --tat-ca >> `"$Logs\lich.log`" 2>&1" (New-ScheduledTaskTrigger -Daily -At 2:30am)
    Add-Task "TinhLai" "$run tinhlai >> `"$Logs\lich.log`" 2>&1" (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3:00am)
    foreach ($n in "Ollama", "Web", "Tunnel") {   # chạy ngay, không cần khởi động lại máy
        if (Get-ScheduledTask -TaskPath $Folder -TaskName $n -ErrorAction SilentlyContinue) {
            Start-ScheduledTask -TaskPath $Folder -TaskName $n
        }
    }
    Write-Host "`nXong. Server khởi động mất ~30 giây; kiểm tra: http://127.0.0.1:8000/api/health"
}

function Show-Status {
    $tasks = Get-ScheduledTask -TaskPath $Folder -ErrorAction SilentlyContinue
    if (-not $tasks) { Write-Host "Chưa cài lịch. Chạy: .\tools\trien_khai.ps1 -CaiLich"; return }
    $tasks | ForEach-Object {
        $i = $_ | Get-ScheduledTaskInfo
        [pscustomobject]@{ Tac_vu = $_.TaskName; Trang_thai = $_.State; Lan_cuoi = $i.LastRunTime;
                           Ket_qua = $i.LastTaskResult; Lan_toi = $i.NextRunTime }
    } | Format-Table -AutoSize
    try {
        $h = Invoke-RestMethod "http://127.0.0.1:8000/api/health" -TimeoutSec 5
        Write-Host "Server: OK | $($h.restaurants) quán | LLM: $($h.llm_provider) | đăng nhập: $($h.auth_required)"
    } catch { Write-Host "Server: chưa phản hồi (xem data\logs\web.log)" }
}

if ($GoLich) {
    Assert-Admin
    Get-ScheduledTask -TaskPath $Folder -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-ScheduledTask -InputObject $_ -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -InputObject $_ -Confirm:$false
        Write-Host "Đã gỡ $($_.TaskName)"
    }
    # dừng hẳn tiến trình con còn sót (server, tunnel) để giải phóng cổng 8000
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and (($_.CommandLine -like "*$Root*" -and $_.CommandLine -like "*api.py*") -or
                             $_.CommandLine -like "*tunnel run $TunnelName*")
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
} elseif ($Tunnel -or $CaiLich) {
    if ($CaiLich) { Assert-Admin }   # chỉ cài lịch chạy ngầm mới cần quyền admin; tạo tunnel thì không
    if ($Tunnel) { Initialize-Tunnel $Tunnel.ToLower() }
    if ($CaiLich) { Install-Schedule }
} else {
    Show-Status
}
