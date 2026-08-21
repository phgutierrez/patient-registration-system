@echo off
setlocal EnableExtensions
title Sistema de Ortopedia - Preparacao local manual

set "LAUNCHER_ROOT=%~dp0"
set "LAUNCHER_PS1=%LAUNCHER_ROOT%launcher_network.ps1"
set "CONFIG_DIR=%LOCALAPPDATA%\PatientRegistrationSystem"
set "SOURCE_CONFIG=%CONFIG_DIR%\network-source.txt"
set "NETWORK_SOURCE="
set "NEW_SOURCE="

echo.
echo ============================================================
echo   Sistema de Ortopedia - acesso local com sincronizacao
echo ============================================================
echo.
echo Use este arquivo somente quando o Windows impedir a execucao
echo do BAT diretamente na pasta compartilhada.
echo.

if not exist "%LAUNCHER_PS1%" (
    echo [ERRO] launcher_network.ps1 nao esta ao lado deste BAT.
    echo Copie os dois arquivos para a mesma pasta local e tente novamente.
    echo.
    pause
    exit /b 2
)

where powershell.exe >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Windows PowerShell nao foi encontrado.
    echo.
    pause
    exit /b 3
)

if exist "%SOURCE_CONFIG%" set /p "NETWORK_SOURCE="<"%SOURCE_CONFIG%"

if defined NETWORK_SOURCE (
    echo Caminho compartilhado salvo:
    echo %NETWORK_SOURCE%
    echo.
    set /p "NEW_SOURCE=Pressione ENTER para reutilizar ou digite outro caminho: "
    if defined NEW_SOURCE set "NETWORK_SOURCE=%NEW_SOURCE%"
) else (
    echo Digite o caminho completo da pasta PatientRegistration na rede.
    echo Exemplo: \\servidor\compartilhamento\PatientRegistration
    echo.
    set /p "NETWORK_SOURCE=Caminho da rede: "
)

if not defined NETWORK_SOURCE (
    echo.
    echo [ERRO] Nenhum caminho foi informado.
    pause
    exit /b 4
)

if not exist "%NETWORK_SOURCE%\PatientRegistration.exe" (
    echo.
    echo [ERRO] PatientRegistration.exe nao foi encontrado em:
    echo %NETWORK_SOURCE%
    echo Verifique a rede e informe a pasta correta.
    pause
    exit /b 5
)

if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%" >nul 2>&1
>"%SOURCE_CONFIG%" echo %NETWORK_SOURCE%

powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%LAUNCHER_PS1%" -SourceRoot "%NETWORK_SOURCE%" %*
set "LAUNCHER_EXIT=%ERRORLEVEL%"

if not "%LAUNCHER_EXIT%"=="0" (
    echo.
    echo [ERRO] O sistema nao foi iniciado. Codigo: %LAUNCHER_EXIT%
    echo Nenhum banco ou dado clinico foi removido.
    echo.
    pause
)

exit /b %LAUNCHER_EXIT%
