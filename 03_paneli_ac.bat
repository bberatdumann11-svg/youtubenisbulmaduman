@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Once 01_kurulum.bat dosyasini calistir.
  pause
  exit /b 1
)

echo Panel aciliyor...
echo Tarayicida otomatik acilmazsa ekrandaki Local URL adresini kopyala.
".venv\Scripts\python.exe" -m streamlit run app.py

pause

