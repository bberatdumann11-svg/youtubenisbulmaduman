@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Python virtual environment hazirlaniyor...
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)

echo [2/3] Paketler yukleniyor...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e ".[dashboard,dev]"

echo [3/3] Kurulum bitti.
echo.
echo Simdi 02_demo_calistir.bat dosyasina cift tiklayarak deneyebilirsin.
pause
