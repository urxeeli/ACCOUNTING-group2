@echo off
setlocal
cd /d "%~dp0"

python -c "import main"
if errorlevel 1 (
    echo Application imports failed. Fix the Python errors above before building.
    pause
    exit /b 1
)

set "BUILD_ID="
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss_fff"') do set "BUILD_ID=%%i"
if not defined BUILD_ID (
    echo Could not generate a unique build directory.
    pause
    exit /b 1
)
set "BUILD_ID=%BUILD_ID%_%RANDOM%"
set "DIST_DIR=%~dp0dist\%BUILD_ID%"
set "WORK_DIR=%~dp0build\%BUILD_ID%"

python -m PyInstaller --clean --noconfirm --onefile --windowed --name AccountingApp --distpath "%DIST_DIR%" --workpath "%WORK_DIR%" "%~dp0main.py"
if errorlevel 1 (
    echo Build failed. Review the PyInstaller errors above.
    pause
    exit /b 1
)

if not exist "%DIST_DIR%\AccountingApp.exe" (
    echo Build completed without creating the expected executable.
    pause
    exit /b 1
)

> "%~dp0dist\latest_build.txt" echo %BUILD_ID%
echo Build successful: dist\%BUILD_ID%\AccountingApp.exe
endlocal
