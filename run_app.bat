@echo off
echo Iniciando o sistema de registro de pacientes...

REM Ativar o ambiente virtual (se existir)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Esperar 2 segundos para garantir que o servidor esteja pronto
timeout /t 2 /nobreak > nul

REM Abrir o navegador padrão na página de login
start http://localhost:5000/login

REM Iniciar o servidor Flask
python run.py

pause
