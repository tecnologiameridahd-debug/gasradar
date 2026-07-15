@echo off
cd /d "%~dp0"
title GasRadar - Precios gasolina USA
echo ================================
echo  GasRadar - Precios de gasolina
echo ================================
echo.

python -c "import fastapi,uvicorn,httpx" 2>nul
if errorlevel 1 (
  echo Instalando dependencias...
  python -m pip install -r requirements.txt
)

echo.
echo Abre en el telefono o PC:
echo   http://127.0.0.1:8787
echo.
echo Ctrl+C para detener.
echo.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8787 --reload
pause
