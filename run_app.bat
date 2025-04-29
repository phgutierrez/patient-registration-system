@echo off
echo Iniciando o sistema de registro de pacientes...

REM Ativar o ambiente virtual (se existir)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Configurar tratamento de CTRL+C
REM Este comando permite que o Python receba o sinal SIGINT corretamente
title Sistema de Registro de Pacientes

REM Esperar 2 segundos para garantir que o servidor esteja pronto
timeout /t 2 /nobreak > nul

REM Abrir o navegador padrão na página de login
start http://localhost:5000/login

REM Iniciar o servidor Flask com tratamento adequado de sinais
python run.py

REM Não é mais necessário o pause aqui, pois o script Python já trata o encerramento
