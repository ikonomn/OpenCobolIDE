param(
    [string]$Python = "python",
    [Parameter(Mandatory=$true)][string]$InnoCompiler,
    [string]$Output = ""
)
$ErrorActionPreference = "Stop"
if ($env:OS -ne "Windows_NT") { throw "Build on Windows 11." }
& $Python -c "import platform, sys; sys.exit(0 if sys.getwindowsversion().build >= 22000 and platform.machine().upper() == 'AMD64' else 1)"
if ($LASTEXITCODE -ne 0) { throw "Use 64-bit x86 Python on Windows 11." }
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
if (-not $Output) { $Output = Join-Path $Repo "dist/windows" }
$Output = (New-Item -ItemType Directory -Force $Output).FullName
$InnoCompiler = (Resolve-Path $InnoCompiler).Path
$Work = Join-Path ([IO.Path]::GetTempPath()) ("cobol-build-" + [guid]::NewGuid())
New-Item -ItemType Directory $Work | Out-Null
Push-Location $Repo
try {
    $Extra = @()
    $Vendor = Join-Path $Work "vendor"
    New-Item -ItemType Directory $Vendor | Out-Null
    foreach ($Module in @("pyqode", "qcrash", "qdarkstyle", "keyring")) {
        Copy-Item -Recurse (Join-Path $Repo "open_cobol_ide/extlibs/$Module") $Vendor
    }
    $Extra = @("--paths", $Vendor, "--collect-submodules", "pyqode",
               "--collect-submodules", "qcrash", "--collect-all", "qdarkstyle",
               "--hidden-import", "PyQt5.QtNetwork",
               "--add-data", "${Repo}/doc/OpenCobolIDE-modern12.html:doc",
               "--add-data", "${Repo}/open_cobol_ide/build_tools:open_cobol_ide/build_tools",
               "--icon", (Join-Path $Repo "forms/rc/silex-icon.ico"))
    & $Python -m PyInstaller --noconfirm --onefile --console --noupx --name opencobolide `
        --paths $Repo --distpath $Output --workpath (Join-Path $Work "build") `
        --specpath $Work @Extra (Join-Path $PSScriptRoot "launcher.py")
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed. Build work is in $Work" }
    $Binary = Join-Path $Output "opencobolide.exe"
    & $InnoCompiler "/DAppBinary=$Binary" "/O$Output" (Join-Path $PSScriptRoot "installer.iss")
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed. Build work is in $Work" }
    $Installer = Join-Path $Output "OpenCobolIDE-modern12-win11-x64-setup.exe"
    $Hashes = Get-FileHash -Algorithm SHA256 $Binary,$Installer
    $Hashes | ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path -Leaf $_.Path)" } |
        Set-Content -Encoding ascii (Join-Path $Output "SHA256SUMS")
    Write-Host "Build artifacts: $Output"
} finally {
    Pop-Location
}
