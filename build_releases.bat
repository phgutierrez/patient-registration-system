@echo off
REM Script de compilação para releases 32 bits e 64 bits
REM Sistema de Registro de Pacientes

setlocal enabledelayedexpansion

echo.
echo ========================================================================
echo   COMPILADOR DE RELEASES - Sistema de Registro de Pacientes
echo   Versoes: 32 bits e 64 bits
echo ========================================================================
echo.

REM Verificar se Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao foi encontrado!
    echo Instale Python e adicione ao PATH
    pause
    exit /b 1
)

echo Verificando requisitos...

REM Verificar PyInstaller
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo.
    echo AVISO: PyInstaller nao esta instalado!
    echo Instalando PyInstaller...
    python -m pip install pyinstaller
)

REM Verificar Waitress
python -m pip show waitress >nul 2>&1
if errorlevel 1 (
    echo.
    echo AVISO: Waitress nao esta instalado!
    echo Instalando Waitress...
    python -m pip install waitress
)

echo.
echo Requisitos verificados. Iniciando compilacao...
echo.

REM Executar o script Python de compilação
python build_releases.py

if errorlevel 1 (
    echo.
    echo ERRO: A compilacao falhou!
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   COMPILACAO CONCLUIDA COM SUCESSO!
echo ========================================================================
echo.
echo Proximos passos:
echo   1. Verifique a pasta dist\ para os arquivos compilados
echo   2. Comprima cada pasta (64bits e 32bits) em .zip
echo   3. Distribua os arquivos para os usuarios
echo.

pause
