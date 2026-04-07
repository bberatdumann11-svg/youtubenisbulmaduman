@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Once 01_kurulum.bat dosyasini calistir.
  pause
  exit /b 1
)

set /p APP_PASSWORD=Bu internet paneli icin bir sifre belirle ve Enter'a bas: 
if "%APP_PASSWORD%"=="" (
  echo Sifre bos olamaz. Internetten acarken sifre kullanmak daha guvenli.
  pause
  exit /b 1
)

if not exist "tools" mkdir tools
if not exist "tools\cloudflared.exe" (
  echo Internet linki olusturma araci indiriliyor...
  powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'tools\cloudflared.exe'"
)

echo.
echo Panel ayri bir pencerede aciliyor...
start "YouTube Nis Radar" cmd /k ".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true

timeout /t 5 >nul

echo.
echo Birazdan ekranda https ile baslayan bir link goreceksin.
echo O linki kopyalayip internetten erismek istedigin cihazda acabilirsin.
echo Panel senden biraz once belirledigin sifreyi isteyecek.
echo.
"tools\cloudflared.exe" tunnel --url http://127.0.0.1:8501

pause

