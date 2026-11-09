@echo off
rem Build script untuk 8 Ball Pool Aim Assistant -> .exe (Windows)
rem Jalankan di Windows dengan Python terinstall.

echo [1/4] Memastikan dependensi terinstall...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Gagal install requirements.txt
    pause
    exit /b 1
)

echo [2/4] Install PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo Gagal install PyInstaller
    pause
    exit /b 1
)

echo [3/4] Membersihkan build lama (jika ada)...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist 8BallPoolAimAssistant.spec del /q 8BallPoolAimAssistant.spec

echo [4/4] Membuat .exe (single file, tanpa konsol)...
pyinstaller --onefile --windowed --name "8BallPoolAimAssistant" --add-data "config.json;." --add-data "core;core" main.py
if %errorlevel% neq 0 (
    echo Gagal build .exe
    pause
    exit /b 1
)

echo.
echo ============================================
echo BERHASIL! File .exe ada di:
echo   dist\8BallPoolAimAssistant.exe
echo ============================================
echo.
echo Catatan: pastikan config.json dan folder core/
echo berada di folder yang sama dengan .exe saat
echo dijalankan.
echo.
pause
