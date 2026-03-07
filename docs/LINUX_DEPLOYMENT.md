# Implantação Linux em Rede Hospitalar

Este guia descreve o fluxo recomendado para produção Linux:
- Banco PostgreSQL
- Aplicação Python com Gunicorn
- Serviço gerenciado por systemd
- Exposição via Nginx na rede LAN

## 1) Pré-requisitos

- Ubuntu/Debian, RHEL ou equivalente
- Python 3.9+
- PostgreSQL disponível (local ou remoto)
- unixODBC instalado (pyodbc é obrigatório)

Exemplo Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql-client unixodbc unixodbc-dev nginx
```

## 2) Configurar projeto

```bash
cd /opt/patient-registration-system
bash linux/setup_linux.sh
```

O setup valida:
- `SECRET_KEY` não padrão
- `DATABASE_URL` no formato PostgreSQL
- dependências de ODBC
- migrações (`flask db upgrade`)
- seed idempotente (`setup_init_data.py`)

## 3) Configurar serviço systemd

Arquivo de modelo:
- `linux/systemd/patient-registration.service`

Instalação:

```bash
sudo cp linux/systemd/patient-registration.service /etc/systemd/system/patient-registration.service
sudo systemctl daemon-reload
sudo systemctl enable patient-registration
sudo systemctl start patient-registration
sudo systemctl status patient-registration
```

Logs:

```bash
sudo journalctl -u patient-registration -f
```

## 4) Configurar Nginx

Arquivo de modelo:
- `linux/nginx/patient-registration.conf`

Instalação:

```bash
sudo cp linux/nginx/patient-registration.conf /etc/nginx/sites-available/patient-registration
sudo ln -s /etc/nginx/sites-available/patient-registration /etc/nginx/sites-enabled/patient-registration
sudo nginx -t
sudo systemctl reload nginx
```

## 5) Firewall (LAN)

Exemplo UFW para liberar HTTP apenas na sub-rede hospitalar:

```bash
sudo ufw allow from 192.168.0.0/16 to any port 80 proto tcp
sudo ufw deny 5000/tcp
```

> Recomendado manter Gunicorn apenas em `127.0.0.1:5000` e publicar para clientes via Nginx.

## 6) Variáveis obrigatórias no `.env`

```properties
SECRET_KEY=chave-unica-gerada-para-o-hospital
DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/patient_registration
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DESKTOP_MODE=false
FLASK_ENV=production
FLASK_DEBUG=0
```

## 7) Operação

- Iniciar manualmente (fallback): `bash linux/run_network.sh`
- Iniciar padrão produção: `systemctl start patient-registration` + Nginx
- Atualização: backup de banco, atualizar código, `pip install -r requirements.txt`, `flask db upgrade`, reiniciar serviço
