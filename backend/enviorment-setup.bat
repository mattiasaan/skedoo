```bat
@echo off
setlocal

cd /d "%~dp0"

echo [1/4] Creazione ambiente virtuale...
py -m venv .venv
if errorlevel 1 goto :error

echo [2/4] Attivazione ambiente virtuale...
call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo [3/4] Installazione dipendenze...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [4/4] Installazione dipendenze di sviluppo...
python -m pip install -r requirements-dev.txt
if errorlevel 1 goto :error

echo.
echo Setup completato con successo!
pause
exit /b 0

:error
echo.
echo ERRORE durante l'esecuzione del setup.
pause
exit /b 1
```