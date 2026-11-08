# Read-only collection for the one authorized FroggerPro; no reboot, root, flash or erase.
param(
    [string]$AdbPath = 'C:\Users\REaps\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe',
    [string]$OutputDirectory = (Join-Path (Get-Location) ('frogger-runtime-' + (Get-Date -Format yyyyMMdd-HHmmss)))
)
$ErrorActionPreference = 'Stop'
$Serial = '003383663003343'
$Devices = & $AdbPath devices
if (!($Devices -match "^$Serial\s+device$")) { throw 'Authorized FroggerPro is not connected through ADB. No phone changes made.' }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
function Capture([string]$Name, [string[]]$Arguments) {
    & $AdbPath -s $Serial @Arguments 2>&1 | Out-File -LiteralPath (Join-Path $OutputDirectory $Name) -Encoding utf8
    if ($LASTEXITCODE -ne 0) { Write-Warning "Collection incomplete: $Name (ADB exit $LASTEXITCODE)" }
}
Capture 'identity.txt' @('shell', 'id; cat /proc/uptime; getprop sys.boot_completed; getprop ro.build.fingerprint; getprop ro.boot.slot_suffix; getenforce; pidof system_server; pidof com.android.phone; pidof com.qti.phone')
Capture 'services.txt' @('shell', 'service list; dumpsys fingerprint; dumpsys activity lastanr; dumpsys bluetooth_manager')
Capture 'radio-process.txt' @('shell', 'getprop | grep -i -E "qcril|radio|multisim"; radio_pid=$(getprop init.svc_debug_pid.vendor.qcrild); if [ -n "$radio_pid" ]; then cat /proc/$radio_pid/maps; fi; cat /vendor/etc/init/qcrilNrd.rc; cat /vendor/etc/vintf/manifest/android.hardware.radio.data.xml')
Capture 'fingerprint-files.txt' @('shell', 'ls -lZ /vendor/bin/hw/vendor.nothing.hardware.biometrics.fingerprint-service /vendor/lib64/hw/fingerprint.default.so /dev/goodix_fp; sha256sum /vendor/lib64/hw/fingerprint.default.so; ps -AZ | grep -i fingerprint')
Capture 'logcat-all.txt' @('logcat', '-b', 'all', '-d', '-v', 'threadtime')
Capture 'logcat-radio.txt' @('logcat', '-b', 'radio', '-d', '-v', 'threadtime')
Write-Host "Saved read-only runtime evidence: $OutputDirectory"
