@echo off
setlocal enabledelayedexpansion
title Sistema de Registro de Pacientes

REM =====================================================
REM Verificar se Python existe; se nao, instalar 3.11.9
REM =====================================================

where py >nul 2>nul
if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python nao encontrado. Instalando Python 3.11.9 (modo usuario)...

        set "PYTHON_VERSION=3.11.9"
        set "PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe"
        set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_INSTALLER%"

        echo Baixando instalador...
        curl -L "%PYTHON_URL%" -o "%PYTHON_INSTALLER%"
        if errorlevel 1 goto :error

        echo Instalando Python 3.11.9 para o usuario atual...
        "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
        if errorlevel 1 goto :error

        echo Python instalado com sucesso.
        del "%PYTHON_INSTALLER%"
        echo Recarregando ambiente...
        timeout /t 5 >nul
    )
)


echo Verificando Python...
set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py -3"

if not defined PY_CMD (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python nao encontrado. Instale o Python 3 e tente novamente.
        pause
        exit /b 1
    ) else (
        set "PY_CMD=python"
    )
)

for /f "tokens=2" %%v in ('!PY_CMD! --version 2^>^&1') do set "PY_VERSION=%%v"
echo Python detectado: !PY_VERSION!

set "VENV_DIR=venv"
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Criando ambiente virtual em %VENV_DIR%...
    !PY_CMD! -m venv "%VENV_DIR%" || goto :error
)

call "%VENV_DIR%\Scripts\activate.bat" || goto :error

echo Atualizando pip...
python -m pip install --upgrade pip || goto :error

if exist requirements.txt (
    echo Instalando dependencias de requirements.txt...
    python -m pip install -r requirements.txt || goto :error
) else (
    echo Arquivo requirements.txt nao encontrado; pulando instalacao de dependencias.
)

echo.
echo Iniciando o servidor Flask...
echo Aguarde enquanto o servidor inicia em http://localhost:5000/
echo.

REM Iniciar o servidor em uma janela separada
start "Servidor Flask" python run.py

REM Aguardar 5 segundos para o servidor estar pronto
timeout /t 5 /nobreak

REM Abrir navegador
start http://localhost:5000/

REM Encerrar este script
exit /b 0

:error
echo.
echo Ocorreu um erro ao iniciar ou executar o sistema.
pause
exit /b 1

:end
echo Servidor finalizado.
pause
exit /b 0
