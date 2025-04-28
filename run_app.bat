@echo off
REM Muda para o diretório onde o script .bat está localizado
cd /d "%~dp0"

REM Ativa o ambiente virtual (ajuste 'venv' se o nome for diferente)
IF EXIST venv\Scripts\activate (
    echo Ativando ambiente virtual 'venv'...
    call venv\Scripts\activate
) ELSE (
    echo AVISO: Ambiente virtual 'venv' nao encontrado. Tentando rodar sem ele.
)

REM Define a aplicação Flask (ajuste o caminho se app.py estiver em outro lugar)
set FLASK_APP=src/app.py

REM Define o modo de desenvolvimento para habilitar debug e reload
set FLASK_ENV=development

REM Abre a página de login no navegador padrão
echo Abrindo a pagina de login no navegador...
start "" http://localhost:5000/login

REM Roda a aplicação Flask
echo Iniciando servidor Flask...
flask run

REM Pausa no final se desejar ver alguma mensagem antes de fechar (opcional)
REM pause 