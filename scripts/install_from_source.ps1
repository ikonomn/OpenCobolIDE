param(
    [string]$VenvDir = ".venv"
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $RepoDir $VenvDir

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -m venv $VenvPath
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python -m venv $VenvPath
}
else {
    throw "Python 3 was not found. Install Python and add it to PATH."
}

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip setuptools wheel
& $VenvPython -m pip install $RepoDir

Write-Host ""
Write-Host "OpenCobolIDE was installed in: $VenvPath"
Write-Host "Run it with: $VenvPath\Scripts\opencobolide.exe"

if (-not (Get-Command cobc -ErrorAction SilentlyContinue)) {
    Write-Warning "cobc.exe was not found in PATH. Install GnuCOBOL before compiling."
}
