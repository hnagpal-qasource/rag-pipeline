param()
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  Write-Error "Missing venv python at $venvPython"
}

$logDir = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "streamlit.log"

Write-Host "Starting Streamlit on http://127.0.0.1:8501"
Write-Host "Logging to $logFile"

& $venvPython -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.fileWatcherType none --logger.level debug *>&1 | Tee-Object -FilePath $logFile
