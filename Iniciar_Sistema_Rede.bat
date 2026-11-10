@echo off
setlocal EnableExtensions
title Sistema de Ortopedia v2.7.0 - Inicializacao local

set "LAUNCHER_ROOT=%~dp0"
set "LAUNCHER_PS1=%LAUNCHER_ROOT%launcher_network.ps1"

echo.
echo ============================================================
echo   Sistema de Ortopedia v2.7.0 - copia local segura
echo ============================================================
echo.

if not exist "%LAUNCHER_PS1%" (
    echo [ERRO] Arquivo launcher_network.ps1 nao encontrado.
    echo        Mantenha o BAT, o PS1, o EXE e a pasta _internal juntos.
    echo.
    pause
    exit /b 2
)

where powershell.exe >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Windows PowerShell nao foi encontrado neste computador.
    echo        Solicite ao suporte de TI a liberacao do PowerShell 5.1.
    echo.
    pause
    exit /b 3
)

powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%LAUNCHER_PS1%" %*
set "LAUNCHER_EXIT=%ERRORLEVEL%"

if not "%LAUNCHER_EXIT%"=="0" (
    echo.
    echo [ERRO] O sistema nao foi iniciado. Codigo: %LAUNCHER_EXIT%
    echo Consulte o guia LEIA-ME_ACESSO_REDE.txt nesta mesma pasta.
    echo.
    pause
)

exit /b %LAUNCHER_EXIT%
