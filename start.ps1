$pythonExe = "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe"
if (-not (Test-Path $pythonExe)) {
    $found = Get-Command py, python -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
    if ($found) { $pythonExe = $found }
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Egypt SDGs Knowledge Assistant | مساعد المعرفة" -ForegroundColor Cyan
Write-Host "  Using Python: $pythonExe" -ForegroundColor Yellow
Write-Host "  Opening http://localhost:8000 ..." -ForegroundColor Green
Write-Host "============================================================"

Start-Process "http://localhost:8000"
& $pythonExe run.py
