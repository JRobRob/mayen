@echo off
cd /d "%~dp0"
echo.
echo MAYEN V PETAPA - servidor local
echo ================================
echo.
echo Abre en tu navegador: http://localhost:8000
echo Para cerrar, presiona Ctrl+C en esta ventana.
echo.
start "" http://localhost:8000
py -m http.server 8000 2>nul || python -m http.server 8000
pause
