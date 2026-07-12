@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Build Patient Registration - Windows 32 bits
echo ================================================================
echo  BUILD DO EXECUTAVEL - WINDOWS 32 BITS
echo ================================================================
echo.

if not exist "build_exe_32bits.py" goto :bad_folder
if not exist "requirements.txt" goto :bad_folder
if not exist "server.py" goto :bad_folder

set "VENV_PYTHON=.venv32\Scripts\python.exe"

if exist "%VENV_PYTHON%" goto :validate_venv

echo [1/5] Ambiente Python 32 bits nao encontrado. Criando .venv32...

if defined PYTHON32_EXE (
    if not exist "%PYTHON32_EXE%" goto :bad_python_override
    "%PYTHON32_EXE%" -c "import struct,sys; raise SystemExit(0 if struct.calcsize('P')*8 == 32 and sys.version_info >= (3,10) else 1)"
    if errorlevel 1 goto :bad_python_override
    "%PYTHON32_EXE%" -m venv .venv32
    if errorlevel 1 goto :venv_failed
    goto :validate_venv
)

where py >nul 2>&1
if errorlevel 1 goto :no_python32

py -3.11-32 -c "import struct,sys; raise SystemExit(0 if struct.calcsize('P')*8 == 32 and sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3.11-32 -m venv .venv32
    if errorlevel 1 goto :venv_failed
    goto :validate_venv
)

py -3.10-32 -c "import struct,sys; raise SystemExit(0 if struct.calcsize('P')*8 == 32 and sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3.10-32 -m venv .venv32
    if errorlevel 1 goto :venv_failed
    goto :validate_venv
)

py -3.12-32 -c "import struct,sys; raise SystemExit(0 if struct.calcsize('P')*8 == 32 and sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3.12-32 -m venv .venv32
    if errorlevel 1 goto :venv_failed
    goto :validate_venv
)

goto :no_python32

:validate_venv
echo [2/5] Validando ambiente virtual...
if not exist "%VENV_PYTHON%" goto :venv_failed
"%VENV_PYTHON%" -c "import struct,sys; print('Python', sys.version.split()[0], '-', struct.calcsize('P')*8, 'bits'); raise SystemExit(0 if struct.calcsize('P')*8 == 32 and sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto :wrong_architecture

echo [3/5] Atualizando ferramentas de instalacao...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :dependency_failed

echo [4/5] Instalando dependencias do projeto...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :dependency_failed
"%VENV_PYTHON%" -m pip check
if errorlevel 1 goto :dependency_failed
"%VENV_PYTHON%" -c "import PyInstaller, pymupdf, struct; assert struct.calcsize('P')*8 == 32; assert hasattr(pymupdf.Document, 'bake')"
if errorlevel 1 goto :dependency_failed

echo [5/5] Gerando e validando o executavel...
echo.
"%VENV_PYTHON%" build_exe_32bits.py
set "BUILD_RESULT=%ERRORLEVEL%"
if not "%BUILD_RESULT%"=="0" goto :build_failed

echo.
echo ================================================================
echo  [OK] BUILD 32 BITS CONCLUIDO E VALIDADO
echo ================================================================
echo  Saida: dist\Sistema32bits\PatientRegistration\
echo  EXE:   dist\Sistema32bits\PatientRegistration\PatientRegistration.exe
echo.
pause
exit /b 0

:bad_folder
echo [ERRO] Execute este batch dentro da pasta completa do projeto.
goto :failed

:bad_python_override
echo [ERRO] PYTHON32_EXE nao aponta para um Python 3.10+ de 32 bits:
echo        %PYTHON32_EXE%
goto :failed

:no_python32
echo [ERRO] Nenhum Python 3.10+ de 32 bits foi encontrado.
echo.
echo Instale o Python 3.11 Windows 32-bit com o Python Launcher.
echo Como alternativa, defina antes de executar:
echo   set "PYTHON32_EXE=C:\caminho\python.exe"
echo   build_exe_32bits.bat
goto :failed

:venv_failed
echo [ERRO] Nao foi possivel criar ou localizar .venv32.
goto :failed

:wrong_architecture
echo [ERRO] A pasta .venv32 existe, mas nao usa Python 3.10+ de 32 bits.
echo Renomeie ou remova .venv32 e execute este batch novamente.
goto :failed

:dependency_failed
echo [ERRO] Falha ao instalar ou validar as dependencias de 32 bits.
echo Verifique a conexao e as mensagens apresentadas acima.
goto :failed

:build_failed
echo.
echo [ERRO] O build ou a autoverificacao falhou. Codigo: %BUILD_RESULT%
echo Consulte tambem logs\patient-registration.log, se disponivel.
goto :failed_with_code

:failed
set "BUILD_RESULT=1"

:failed_with_code
echo.
pause
exit /b %BUILD_RESULT%
