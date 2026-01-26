@echo off
REM ============================================================================
REM  Script de Compilacao - Prontuario de Pacientes v1.0.1
REM  Para: Windows 7 ou superior
REM  Requerimentos: Python 3.7+, pip, PyInstaller 6.10.0+
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo.
echo   Compilador de Release - Prontuario v1.0.1
echo   Data: 26 de janeiro de 2026
echo.
echo ============================================================================
echo.

REM Verificar se estamos no diretorio correto
if not exist "prontuario_64bits.spec" (
    echo ERRO: Arquivo prontuario_64bits.spec nao encontrado
    echo        Certifique-se de executar este script no diretorio raiz do projeto
    pause
    exit /b 1
)

echo [1/5] Validando ambiente Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado
    echo       Instale Python 3.7+ e adicione ao PATH
    pause
    exit /b 1
)

python -m pip show PyInstaller >nul 2>&1
if errorlevel 1 (
    echo AVISO: PyInstaller nao instalado
    echo        Instalando PyInstaller>=6.10.0...
    python -m pip install "PyInstaller>=6.10.0" --upgrade
)

python -m pip show waitress >nul 2>&1
if errorlevel 1 (
    echo AVISO: Waitress nao instalado
    echo        Instalando waitress==2.1.2...
    python -m pip install waitress==2.1.2
)

echo [OK] Ambiente Python validado
echo.

echo [2/5] Compilando Build 64-bits...
echo        (Isto pode levar 10-15 minutos)
echo.
python -m PyInstaller --clean prontuario_64bits.spec
if errorlevel 1 (
    echo ERRO na compilacao 64-bits
    pause
    exit /b 1
)
echo [OK] Build 64-bits compilado
echo.

echo [3/5] Compilando Build 32-bits...
echo        (Isto pode levar 10-15 minutos)
echo.
python -m PyInstaller --clean prontuario_32bits.spec
if errorlevel 1 (
    echo ERRO na compilacao 32-bits
    pause
    exit /b 1
)
echo [OK] Build 32-bits compilado
echo.

echo [4/5] Criando arquivos ZIP...
cd dist

REM Comprimir 64 bits
echo        Compactando 64-bits...
if exist prontuario-v1.0.1-64bits.zip del prontuario-v1.0.1-64bits.zip
powershell -Command "Compress-Archive -Path '64bits/prontuario-64bits' -DestinationPath 'prontuario-v1.0.1-64bits.zip' -Force"
if errorlevel 1 (
    echo ERRO ao comprimir 64-bits
    cd ..
    pause
    exit /b 1
)

REM Comprimir 32 bits
echo        Compactando 32-bits...
if exist prontuario-v1.0.1-32bits.zip del prontuario-v1.0.1-32bits.zip
powershell -Command "Compress-Archive -Path '32bits/prontuario-32bits' -DestinationPath 'prontuario-v1.0.1-32bits.zip' -Force"
if errorlevel 1 (
    echo ERRO ao comprimir 32-bits
    cd ..
    pause
    exit /b 1
)

echo [OK] Arquivos ZIP criados
echo.

echo [5/5] Verificando resultado...
if exist "prontuario-v1.0.1-64bits.zip" (
    for %%A in (prontuario-v1.0.1-64bits.zip) do set size1=%%~zA
    echo        64-bits: prontuario-v1.0.1-64bits.zip (!size1! bytes^)
) else (
    echo        ERRO: prontuario-v1.0.1-64bits.zip nao encontrado
)

if exist "prontuario-v1.0.1-32bits.zip" (
    for %%A in (prontuario-v1.0.1-32bits.zip) do set size2=%%~zA
    echo        32-bits: prontuario-v1.0.1-32bits.zip (!size2! bytes^)
) else (
    echo        ERRO: prontuario-v1.0.1-32bits.zip nao encontrado
)

echo.
echo ============================================================================
echo.
echo   SUCESSO! Compilacao concluida.
echo.
echo   Arquivos de Release Criados:
echo   - prontuario-v1.0.1-64bits.zip
echo   - prontuario-v1.0.1-32bits.zip
echo.
echo   PROXIMA ETAPA: Upload para GitHub Release
echo.
echo   1. Acesse: https://github.com/phgutierrez/patient-registration-system/releases
echo   2. Clique em "Draft a new release"
echo   3. Selecione tag: v1.0.1
echo   4. Preencha titulo e descricao
echo   5. Arraste os 2 arquivos ZIP para "Attach binaries"
echo   6. Clique em "Publish release"
echo.
echo   Consulte GITHUB_RELEASE_GUIDE.md para mais detalhes.
echo.
echo ============================================================================
echo.

cd ..
echo Pressione uma tecla para fechar...
pause >nul
