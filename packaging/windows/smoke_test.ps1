# The Windows installer's own test, run on GitHub's Windows runner (M13 Part W, specification §5.2).
#
# Installs silently for the current user, checks the Start-menu entry and the MCP program, starts the
# installed app with no browser, fetches /healthz and the first page through a fresh launch link,
# stops it, uninstalls it, and checks that a review folder made before the test is still there.
#
# Both the app's home AND the reviews folder point at temporary folders: NEXUS_APP_HOME alone would
# leave the reviews folder at the default (~\Documents\Nexus Scholar\workspaces), a real one on any
# computer but a fresh runner (M13 Part B, the coordinator's note on the check by hand).
param(
    [Parameter(Mandatory = $true)][string]$Installer
)
$ErrorActionPreference = "Stop"

function Wait-Until([scriptblock]$Condition, [int]$Seconds, [string]$What) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while (-not (& $Condition)) {
        if ((Get-Date) -gt $deadline) { throw "timed out after $Seconds s waiting for: $What" }
        Start-Sleep -Milliseconds 250
    }
}

$base = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$root = Join-Path $base "ns-smoke"
if (Test-Path $root) { Remove-Item -Recurse -Force $root }
New-Item -ItemType Directory -Force (Join-Path $root "home"), (Join-Path $root "workspaces\kept-review") | Out-Null
Set-Content -Path (Join-Path $root "workspaces\kept-review\note.txt") -Value "made before the install"
$env:NEXUS_APP_HOME = Join-Path $root "home"
$env:NEXUS_WORKSPACES_ROOT = Join-Path $root "workspaces"
$env:NEXUS_APP_DIALOGS = "0"
$settings = Join-Path $root "home\settings"
$summary = @()

# 1. Install, per user, silently.
$installerBytes = (Get-Item $Installer).Length
$p = Start-Process -FilePath $Installer -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", "/LOG=$root\install.log" -Wait -PassThru
if ($p.ExitCode -ne 0) { Get-Content "$root\install.log" -Tail 40; throw "the installer failed with exit code $($p.ExitCode)" }
$app = Join-Path $env:LOCALAPPDATA "Programs\Nexus Scholar"
$exe = Join-Path $app "Nexus Scholar.exe"
if (-not (Test-Path $exe)) { throw "no $exe after the install" }
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Nexus Scholar"
if (-not (Get-ChildItem -Path $startMenu -Filter "*.lnk" -ErrorAction SilentlyContinue)) { throw "no Start-menu entry under $startMenu" }
$installedBytes = (Get-ChildItem -Recurse -File $app | Measure-Object -Sum Length).Sum
$summary += "installer: {0:N1} MB; installed: {1:N1} MB" -f ($installerBytes / 1MB), ($installedBytes / 1MB)

# 2. The MCP program answers.
& (Join-Path $app "nexus-scholar-mcp.exe") --help | Out-Null
if ($LASTEXITCODE -ne 0) { throw "nexus-scholar-mcp.exe --help failed with $LASTEXITCODE" }

# 3. Start with no browser; the engine publishes engine.json once it answers.
$t0 = Get-Date
Start-Process -FilePath $exe -ArgumentList "--no-browser" -WorkingDirectory $env:SystemRoot | Out-Null
Wait-Until { Test-Path (Join-Path $settings "engine.json") } 120 "the engine to answer"
$info = Get-Content (Join-Path $settings "engine.json") -Raw | ConvertFrom-Json
$origin = "http://127.0.0.1:$($info.port)"
$health = Invoke-WebRequest -UseBasicParsing "$origin/healthz"
if ($health.StatusCode -ne 200) { throw "/healthz answered $($health.StatusCode)" }
# A fresh one-time link, as a second click on the icon asks for one (the secret is read here, never printed).
$link = Invoke-RestMethod -Method Post -Uri "$origin/instance/launch-link" -Headers @{ "X-Nexus-Instance" = $info.secret } -ContentType "application/json" -Body "{}"
$page = Invoke-WebRequest -UseBasicParsing -Uri $link.url -SessionVariable session
if ($page.StatusCode -ne 200) { throw "the first page answered $($page.StatusCode)" }
$firstPage = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
$landing = $page.BaseResponse.ResponseUri
if (-not $landing) { $landing = $page.BaseResponse.RequestMessage.RequestUri }
$summary += "first page after $firstPage s ($landing)"
if ("$landing" -notmatch "/en/settings/") { throw "the first run did not open setup: $landing" }

# 4. Stop it with a second program start, as the installer's "stop it first" does.
Start-Process -FilePath $exe -ArgumentList "--stop" -Wait | Out-Null
Wait-Until { -not (Test-Path (Join-Path $settings "engine.json")) } 60 "the engine to stop"
if (Get-NetTCPConnection -LocalPort $info.port -State Listen -ErrorAction SilentlyContinue) { throw "port $($info.port) still listens after the stop" }

# 5. Uninstall silently; the review and (on a silent uninstall) the settings stay.
$uninstaller = Get-ChildItem -Path $app -Filter "unins*.exe" | Select-Object -First 1
Start-Process -FilePath $uninstaller.FullName -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART" -Wait | Out-Null
Wait-Until { -not (Test-Path $exe) } 120 "the uninstaller to remove the program"
if (-not (Test-Path (Join-Path $root "workspaces\kept-review\note.txt"))) { throw "the uninstall removed a review" }
if (-not (Test-Path (Join-Path $settings "settings.json")) -and -not (Test-Path $settings)) { throw "a silent uninstall removed the settings" }
if (Get-ChildItem -Path $startMenu -Filter "*.lnk" -ErrorAction SilentlyContinue) { throw "the Start-menu entry is still there" }

$summary += "installed, started, stopped and uninstalled; the review kept"
$summary | ForEach-Object { Write-Host $_ }
if ($env:GITHUB_STEP_SUMMARY) { $summary | ForEach-Object { "- $_" } | Out-File -Append -Encoding utf8 $env:GITHUB_STEP_SUMMARY }
