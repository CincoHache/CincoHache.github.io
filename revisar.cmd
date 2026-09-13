@echo off
rem  Compila el blog y lo revisa, igual que hace GitHub al publicar.
rem  Doble clic aqui antes de subir nada y te ahorras el viaje.
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo   Compilando...
call bundle exec jekyll build --quiet
if errorlevel 1 (
  echo.
  echo   La compilacion ha fallado. Mira el error de arriba.
  pause
  exit /b 1
)

python _pruebas\revisar.py _site
if errorlevel 1 (
  echo.
  echo   No lo subas todavia: arregla lo de arriba.
  pause
  exit /b 1
)

echo.
echo   Todo en orden. Se puede subir.
pause
