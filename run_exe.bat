@echo off
REM Script para executar o Patient Registration System

echo ================================================
echo   Patient Registration System
echo   Servidor de Produção com Waitress
echo ================================================
echo.

REM Verificar se o executável existe
if exist "dist\PatientRegistration.exe" (
    echo Iniciando aplicação...
    echo.
    echo O servidor estará disponível em: http://127.0.0.1:5000
    echo Pressione CTRL+C para parar o servidor
    echo.
    "dist\PatientRegistration.exe"
) else (
    echo ERRO: Executável não encontrado!
    echo.
    echo Execute primeiro: python build_exe.py
    echo.
    pause
)
