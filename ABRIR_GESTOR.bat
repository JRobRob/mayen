@echo off
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python gestor.py
  goto :eof
)
where py >nul 2>nul
if %errorlevel%==0 (
  py gestor.py
  goto :eof
)
echo.
echo No se encontro Python en este equipo.
echo Instala Python 3 y luego vuelve a ejecutar este archivo,
echo o abre PowerShell en esta carpeta y ejecuta: python gestor.py
echo.
pause
