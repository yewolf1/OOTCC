@echo off
cd /d "%~dp0"

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist OOTCC.exe del /f /q OOTCC.exe

python -m PyInstaller --noconfirm --clean --distpath . --workpath build OOTCC.spec

if exist ".\OOTCC.exe" (
    echo.
    echo Build success: "%cd%\OOTCC.exe"
) else (
    echo.
    echo Build failed.
)

pause