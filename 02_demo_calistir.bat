@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Once 01_kurulum.bat dosyasini calistir.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m youtube_niche_researcher.cli --demo

echo.
echo Demo rapor olustu:
echo reports\latest\report.md
echo.
pause

