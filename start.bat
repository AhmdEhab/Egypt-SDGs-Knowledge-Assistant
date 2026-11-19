@echo off
chcp 65001 >nul
title Egypt SDGs Knowledge Assistant
echo ============================================================
echo   مساعد المعرفة لأهداف التنمية المستدامة في مصر
echo   Egypt SDGs Knowledge Assistant
echo ============================================================
echo.

set PYTHON_CMD=

:: 1. Check if python is on PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python
    goto found
)

:: 2. Check py launcher
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
    goto found
)

:: 3. Check default user install location (Python 3.14)
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    goto found
)

:: 4. Search any python under LOCALAPPDATA
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%D\python.exe" (
        set PYTHON_CMD="%%D\python.exe"
        goto found
    )
)

echo [ERROR] لم يتم العثور على بايثون تلقائياً.
echo [ERROR] Could not find Python installation automatically.
pause
exit /b 1

:found
echo [OK] Using Python: %PYTHON_CMD%
echo.
echo جاري تشغيل الخادم وفتح المتصفح على: http://localhost:8000 ...
echo Starting server and opening browser at http://localhost:8000 ...
echo.

:: Open browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

:: Start server
%PYTHON_CMD% run.py

pause
