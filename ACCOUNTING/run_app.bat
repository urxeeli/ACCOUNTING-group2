@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0dist\latest_build.txt" (
    echo No successful build is registered. Run build_app.bat first.
    pause
    exit /b 1
)
set /p "BUILD_ID="<"%~dp0dist\latest_build.txt"
echo(%BUILD_ID%| findstr /r /x "[0-9][0-9]*_[0-9][0-9]*_[0-9][0-9]*_[0-9][0-9]*" >nul
if errorlevel 1 (
    echo The latest-build marker is invalid. Run build_app.bat again.
    pause
    exit /b 1
)
if not exist "%~dp0dist\%BUILD_ID%\AccountingApp.exe" (
    echo The executable for the latest build was not found. Run build_app.bat again.
    pause
    exit /b 1
)
start "" "%~dp0dist\%BUILD_ID%\AccountingApp.exe"
endlocal
