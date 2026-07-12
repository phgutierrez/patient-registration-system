@echo off
setlocal
cd /d "%~dp0"

echo ================================================================
echo  SETUP SEGURO - Patient Registration System
echo ================================================================

where python >nul 2>&1
if errorlevel 1 goto :no_python
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto :bad_python

if not exist "requirements.txt" goto :bad_folder
if not exist ".env.example" goto :bad_folder

if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 goto :failed
)

".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [ERRO] O ambiente .venv usa Python antigo ou esta corrompido.
    echo Renomeie a pasta .venv e execute o setup novamente.
    pause
    exit /b 1
)

echo [SETUP] Atualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed

echo [SETUP] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo [SETUP] Preparando configuracao e banco sem apagar dados...
".venv\Scripts\python.exe" scripts\setup_system.py
if errorlevel 1 goto :failed

echo [SETUP] Executando verificacao final...
".venv\Scripts\python.exe" scripts\verify_setup.py
if errorlevel 1 goto :failed

echo.
echo [OK] Setup concluido.
echo Execute run_local.bat ou run_network.bat.
echo Se nenhum usuario foi criado, abra o sistema neste computador:
echo http://localhost:5000
pause
exit /b 0

:no_python
echo [ERRO] Python nao encontrado. Instale Python 3.11 e marque Add to PATH.
pause
exit /b 1

:bad_python
echo [ERRO] Python 3.10 ou posterior e obrigatorio.
pause
exit /b 1

:bad_folder
echo [ERRO] Execute este arquivo dentro da pasta completa do projeto.
pause
exit /b 1

:failed
echo.
echo [ERRO] Setup interrompido. Os dados existentes nao foram apagados.
echo Consulte as mensagens acima e execute verify_setup.bat.
pause
exit /b 1
