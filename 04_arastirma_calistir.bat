@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Once 01_kurulum.bat dosyasini calistir.
  pause
  exit /b 1
)

set /p YOUTUBE_API_KEY=YouTube erisim anahtarini yaz ve Enter'a bas: 
set /p SEEDS=Ana konulari yaz. Ornek: mythology luxury horror : 

if "%SEEDS%"=="" (
  echo Ana konu girmedin. Ornek: mythology luxury
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m youtube_niche_researcher.cli %SEEDS% --expand --max-results 20 --output-dir reports\latest

echo.
echo Rapor olustu:
echo reports\latest\report.md
echo.
pause
