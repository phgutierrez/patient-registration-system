# filepath: /patient-registration-system/patient-registration-system/README.md

# Sistema de Registro de Pacientes

Sistema para gerenciamento de prontuários, pacientes e solicitações de cirurgia desenvolvido com Flask.

## Funcionalidades

- Cadastro e gerenciamento de pacientes
- Solicitação e agendamento de cirurgias
- Geração automática de PDFs para solicitações
- Integração com Google Forms para agendamento
- Interface responsiva

## Tecnologias Utilizadas

- Python 3.x
- Flask (Framework web)
- SQLAlchemy (ORM)
- Bootstrap (Frontend)
- FillPDF (Preenchimento de formulários PDF)

## Estrutura do Projeto

```
patient-registration-system
├── src
│   ├── static
│   │   ├── css
│   │   │   └── styles.css
│   │   └── js
│   │       └── main.js
│   ├── templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   └── registration.html
│   ├── models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── patient.py
│   ├── routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── patients.py
│   ├── database
│   │   └── schema.sql
│   ├── config.py
│   ├── app.py
│   └── utils.py
├── tests
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_patients.py
├── requirements.txt
└── README.md
```

## Como Instalar e Executar

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/patient-registration-system.git
   cd patient-registration-system
   ```

2. Crie um ambiente virtual e instale as dependências:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Execute o aplicativo:
   ```
   flask run
   ```

4. Acesse o sistema em: http://127.0.0.1:5000