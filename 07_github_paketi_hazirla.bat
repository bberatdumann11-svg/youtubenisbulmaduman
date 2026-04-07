@echo off
setlocal
cd /d "%~dp0"

echo GitHub'a yuklenecek temiz paket hazirlaniyor...

if exist "github_paketi" rmdir /s /q "github_paketi"
if exist "github_paketi.zip" del /q "github_paketi.zip"
mkdir "github_paketi"

robocopy "." "github_paketi" /E ^
  /XD ".git" ".venv" "venv" "tools" "reports" "data" "__pycache__" ".pytest_cache" ".ruff_cache" ".mypy_cache" "github_paketi" "youtube_niche_researcher.egg-info" ^
  /XF ".env" "*.pyc" "github_paketi.zip" >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'github_paketi\*' -DestinationPath 'github_paketi.zip' -Force"

echo.
echo Hazir.
echo GitHub'a yuklerken BU KLASORUN ICINDEKI dosyalari sec:
echo github_paketi
echo.
echo Dikkat: github_paketi.zip dosyasini GitHub'a yukleme. Zip sadece yedek/kolay tasima icin.
echo.
pause
