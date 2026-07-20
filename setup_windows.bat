@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Setup seguro - Patient Registration System
echo ================================================================
echo  SETUP WINDOWS - SOMENTE DEPENDENCIAS BINARIAS
echo ================================================================
echo.

if not exist "requirements.txt" goto :bad_folder
if not exist ".env.example" goto :bad_folder
if not exist "scripts\install_windows_dependencies.py" goto :bad_folder
if not exist "build_support\greenlet-2.0.2-cp311-cp311-win32.whl" goto :wheel_missing

set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import platform,sys; bits=platform.architecture()[0]; ok=sys.implementation.name=='cpython' and sys.version_info[:2]>=(3,10) and not (bits=='32bit' and sys.version_info[:2]!=(3,11)); raise SystemExit(0 if ok else 1)" >nul 2>&1
    if errorlevel 1 goto :replace_venv
    goto :install
)

:create_venv
echo [1/5] Criando ambiente virtual...
if defined PYTHON_EXE (
    if not exist "%PYTHON_EXE%" goto :bad_python_override
    "%PYTHON_EXE%" -c "import platform,sys; bits=platform.architecture()[0]; ok=sys.implementation.name=='cpython' and sys.version_info[:2]>=(3,10) and not (bits=='32bit' and sys.version_info[:2]!=(3,11)); raise SystemExit(0 if ok else 1)"
    if errorlevel 1 goto :bad_python_override
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 goto :venv_failed
    goto :install
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3.11-32 -c "import struct,sys; raise SystemExit(0 if sys.version_info[:2]==(3,11) and struct.calcsize('P')*8==32 else 1)" >nul 2>&1
    if not errorlevel 1 (
        py -3.11-32 -m venv "%VENV_DIR%"
        if errorlevel 1 goto :venv_failed
        goto :install
    )
)

where python >nul 2>&1
if errorlevel 1 goto :no_python
python -c "import platform,sys; bits=platform.architecture()[0]; ok=sys.implementation.name=='cpython' and sys.version_info[:2]>=(3,10) and not (bits=='32bit' and sys.version_info[:2]!=(3,11)); raise SystemExit(0 if ok else 1)"
if errorlevel 1 goto :bad_python
python -m venv "%VENV_DIR%"
if errorlevel 1 goto :venv_failed
goto :install

:replace_venv
echo [AVISO] A pasta .venv usa um Python incompativel e sera preservada.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root=(Resolve-Path -LiteralPath '.').Path; $target=(Resolve-Path -LiteralPath '.venv').Path; if ((Split-Path -Parent $target) -ne $root) { exit 2 }; $backup=Join-Path $root ('.venv_incompativel_' + (Get-Date -Format 'yyyyMMdd_HHmmss')); Move-Item -LiteralPath $target -Destination $backup"
if errorlevel 1 goto :venv_replace_failed
goto :create_venv

:install
echo [2/5] Instalando dependencias sem compilacao C...
"%VENV_PYTHON%" scripts\install_windows_dependencies.py
if errorlevel 1 goto :dependency_failed

echo [3/5] Preparando configuracao e banco sem apagar dados...
"%VENV_PYTHON%" scripts\setup_system.py
if errorlevel 1 goto :setup_failed

echo [4/5] Executando verificacao final...
"%VENV_PYTHON%" scripts\verify_setup.py
if errorlevel 1 goto :verify_failed

echo [5/5] Setup concluido.
echo.
echo [OK] Nenhum compilador ou Visual Build Tools foi utilizado.
echo Execute run_local.bat ou run_network.bat.
echo Se nenhum usuario foi criado, abra http://localhost:5000 neste computador.
pause
exit /b 0

:wheel_missing
echo [ERRO] O wheel binario local do greenlet nao foi encontrado.
echo Restaure a pasta build_support da distribuicao completa.
goto :failure_exit

:no_python
echo [ERRO] Python nao encontrado. Instale CPython 3.11 no perfil do usuario.
goto :failure_exit

:bad_python
echo [ERRO] Python incompativel. Para Windows 32-bit use obrigatoriamente CPython 3.11.
echo Em outras arquiteturas, use uma versao com wheels binarios para todas as dependencias.
goto :failure_exit

:bad_python_override
echo [ERRO] PYTHON_EXE nao aponta para um CPython compativel.
goto :failure_exit

:bad_folder
echo [ERRO] Execute este arquivo dentro da pasta completa do projeto.
goto :failure_exit

:venv_failed
echo [ERRO] Nao foi possivel criar .venv. Verifique a permissao de escrita na pasta.
goto :failure_exit

:venv_replace_failed
echo [ERRO] A .venv incompativel esta aberta ou nao pode ser preservada.
goto :failure_exit

:dependency_failed
echo [ERRO] Falha na instalacao binaria. Consulte build\setup_pip.log.
echo Nenhuma tentativa de compilacao foi permitida.
goto :failure_exit

:setup_failed
echo [ERRO] Falha ao preparar configuracao ou banco. Dados existentes nao foram apagados.
goto :failure_exit

:verify_failed
echo [ERRO] A verificacao final encontrou uma instalacao incompleta.
goto :failure_exit

:failure_exit
echo.
echo Setup interrompido com seguranca.
pause
exit /b 1
