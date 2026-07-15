@echo off
REM Copia este archivo como keep_alive.bat y pon TU URL de Render
set URL=https://TU-APP.onrender.com/api/health
set INTERVAL=600

echo GasRadar keep-alive
echo Ping: %URL%
echo Cada %INTERVAL% segundos. Ctrl+C para parar.
echo.

:loop
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 30; Write-Host (Get-Date -Format 'HH:mm:ss') 'OK' $r.StatusCode $r.Content } catch { Write-Host (Get-Date -Format 'HH:mm:ss') 'FAIL' $_.Exception.Message }"
timeout /t %INTERVAL% /nobreak >nul
goto loop
