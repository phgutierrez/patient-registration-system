@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Build Patient Registration - CPython 3.11 win32
echo ================================================================
echo  BUILD DO EXECUTAVEL - WINDOWS 32 BITS - SEM BUILD TOOLS
echo ================================================================
echo.

if not exist "build_exe_32bits.py" goto :bad_folder
if not exist "requirements.txt" goto :bad_folder
if not exist "server.py" goto :bad_folder

set "VENV_DIR=.venv32"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "GREENLET_WHEEL=build_support\greenlet-2.0.2-cp311-cp311-win32.whl"
set "GREENLET_SHA256=E3C43E42F4BDF29CC18E569B4097F948C0547B0A81C78A291E29169315A3B941"
set "PIP_LOG=build\pip32.log"
set "LAST_BUILD_FILE=build\last_build_32bits.txt"

if not exist "%GREENLET_WHEEL%" goto :wheel_missing
if not exist "build" mkdir "build"

if exist "%VENV_DIR%" (
    if not exist "%VENV_PYTHON%" goto :replace_venv
    "%VENV_PYTHON%" -c "import struct,sys,sysconfig; raise SystemExit(0 if sys.version_info[:2] == (3,11) and struct.calcsize('P')*8 == 32 and sysconfig.get_platform() == 'win32' else 1)" >nul 2>&1
    if errorlevel 1 goto :replace_venv
    goto :validate_venv
)

:create_venv
echo [1/6] Criando ambiente isolado CPython 3.11 32-bit...
if defined PYTHON32_EXE (
    if not exist "%PYTHON32_EXE%" goto :bad_python_override
    "%PYTHON32_EXE%" -c "import struct,sys,sysconfig; raise SystemExit(0 if sys.version_info[:2] == (3,11) and struct.calcsize('P')*8 == 32 and sysconfig.get_platform() == 'win32' else 1)"
    if errorlevel 1 goto :bad_python_override
    "%PYTHON32_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 goto :venv_failed
    goto :validate_venv
)

where py >nul 2>&1
if errorlevel 1 goto :no_python32
py -3.11-32 -c "import struct,sys,sysconfig; raise SystemExit(0 if sys.version_info[:2] == (3,11) and struct.calcsize('P')*8 == 32 and sysconfig.get_platform() == 'win32' else 1)" >nul 2>&1
if errorlevel 1 goto :no_python32
py -3.11-32 -m venv "%VENV_DIR%"
if errorlevel 1 goto :venv_failed
goto :validate_venv

:replace_venv
echo [AVISO] A pasta .venv32 e incompativel e sera preservada com outro nome.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root=(Resolve-Path -LiteralPath '.').Path; $target=(Resolve-Path -LiteralPath '.venv32').Path; if ((Split-Path -Parent $target) -ne $root) { exit 2 }; $backup=Join-Path $root ('.venv32_incompativel_' + (Get-Date -Format 'yyyyMMdd_HHmmss')); Move-Item -LiteralPath $target -Destination $backup"
if errorlevel 1 goto :venv_replace_failed
goto :create_venv

:validate_venv
echo [2/6] Validando Python e arquitetura...
if not exist "%VENV_PYTHON%" goto :venv_failed
"%VENV_PYTHON%" -c "import struct,sys,sysconfig; print('Python', sys.version.split()[0], '-', struct.calcsize('P')*8, 'bits -', sysconfig.get_platform()); raise SystemExit(0 if sys.version_info[:2] == (3,11) and struct.calcsize('P')*8 == 32 and sysconfig.get_platform() == 'win32' else 1)"
if errorlevel 1 goto :wrong_architecture

echo [3/6] Verificando integridade do wheel win32 do greenlet...
"%VENV_PYTHON%" -c "import hashlib,pathlib,sys; p=pathlib.Path(r'%GREENLET_WHEEL%'); actual=hashlib.sha256(p.read_bytes()).hexdigest().upper(); print('SHA-256:', actual); raise SystemExit(0 if actual == r'%GREENLET_SHA256%' else 1)"
if errorlevel 1 goto :wheel_invalid

echo [4/6] Instalando somente pacotes binarios, sem compilacao C...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check --no-deps --force-reinstall "%GREENLET_WHEEL%" --log "%PIP_LOG%"
if errorlevel 1 goto :wheel_install_failed
"%VENV_PYTHON%" -m pip install --disable-pip-version-check --only-binary=:all: -r requirements.txt --log "%PIP_LOG%"
if errorlevel 1 goto :dependency_failed

echo [5/6] Validando dependencias binarias...
"%VENV_PYTHON%" -m pip check
if errorlevel 1 goto :dependency_failed
"%VENV_PYTHON%" -c "import struct,sys,sysconfig,PyInstaller,pymupdf,pyodbc,sqlalchemy; import greenlet; import greenlet._greenlet as gb; assert sys.version_info[:2] == (3,11); assert struct.calcsize('P')*8 == 32; assert sysconfig.get_platform() == 'win32'; assert greenlet.__version__ == '2.0.2'; assert gb.__file__.lower().endswith('.pyd'); assert pyodbc.__file__.lower().endswith('.pyd'); assert hasattr(pymupdf.Document, 'bake'); print('Binarios win32 validados:', gb.__file__, pyodbc.__file__)"
if errorlevel 1 goto :binary_validation_failed

echo [6/6] Gerando e validando o executavel onedir...
echo.
"%VENV_PYTHON%" build_exe_32bits.py
set "BUILD_RESULT=%ERRORLEVEL%"
if not "%BUILD_RESULT%"=="0" goto :build_failed

echo.
echo ================================================================
echo  [OK] BUILD 32 BITS CONCLUIDO SEM VISUAL BUILD TOOLS
echo ================================================================
if exist "%LAST_BUILD_FILE%" (
    echo  EXE gerado em:
    type "%LAST_BUILD_FILE%"
) else (
    echo  Saida criada dentro da pasta dist.
)
echo  Log das dependencias: %PIP_LOG%
echo.
pause
exit /b 0

:bad_folder
echo [ERRO] Execute este batch dentro da pasta completa do projeto.
goto :failed

:wheel_missing
echo [ERRO] Wheel win32 local nao encontrado: %GREENLET_WHEEL%
echo Copie novamente a pasta build_support junto com o projeto.
goto :failed

:wheel_invalid
echo [ERRO] O wheel local do greenlet esta corrompido ou foi alterado.
echo Baixe novamente a pasta completa do projeto.
goto :failed

:bad_python_override
echo [ERRO] PYTHON32_EXE nao aponta para CPython 3.11 32-bit win32:
echo        %PYTHON32_EXE%
goto :failed

:no_python32
echo [ERRO] CPython 3.11 32-bit nao foi encontrado.
echo Instale o Python 3.11 Windows 32-bit no perfil do usuario; nao e necessario ser administrador.
echo Alternativa:
echo   set "PYTHON32_EXE=C:\caminho\python.exe"
echo   build_exe_32bits.bat
goto :failed

:venv_failed
echo [ERRO] Nao foi possivel criar .venv32. Verifique permissao de escrita na pasta do projeto.
goto :failed

:venv_replace_failed
echo [ERRO] A .venv32 incompativel esta aberta ou nao pode ser preservada.
echo Feche processos Python e tente novamente.
goto :failed

:wrong_architecture
echo [ERRO] O ambiente precisa usar exatamente CPython 3.11 32-bit win32.
goto :failed

:wheel_install_failed
echo [ERRO] O wheel greenlet incluido nao e compativel com este Python.
echo Confirme que esta usando CPython 3.11 32-bit. Detalhes: %PIP_LOG%
goto :failed

:dependency_failed
findstr /i /c:"No matching distribution found" "%PIP_LOG%" >nul 2>&1
if not errorlevel 1 echo [ERRO] Uma dependencia nao possui wheel binario compativel com win32.
echo [ERRO] Falha ao instalar ou validar dependencias. Nenhuma compilacao foi tentada.
echo Verifique internet/proxy e consulte: %PIP_LOG%
goto :failed

:binary_validation_failed
echo [ERRO] Uma extensao instalada nao e binaria win32 ou nao pode ser importada.
echo Consulte: %PIP_LOG%
goto :failed

:build_failed
echo.
echo [ERRO] O PyInstaller ou a autoverificacao falhou. Codigo: %BUILD_RESULT%
echo Consulte logs\patient-registration.log quando disponivel.
goto :failed_with_code

:failed
set "BUILD_RESULT=1"

:failed_with_code
echo.
pause
exit /b %BUILD_RESULT%
