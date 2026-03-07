# Quick Start - Instalação e Execução

## Windows (resumido)

```bash
# 1) Entrar na pasta do projeto
cd C:\seu\caminho\patient-registration-system

# 2) Setup inicial
setup_windows.bat

# 3) Executar
run_local.bat    # uso local
run_network.bat  # uso em rede (LAN)
```

Verificação rápida:

```bash
verify_setup.bat
```

---

## Quick Start Linux TI (1 página)

Padrão recomendado para hospital:
- PostgreSQL
- Gunicorn
- systemd
- Nginx

### 1) Pré-requisitos do servidor

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql-client unixodbc unixodbc-dev nginx
```

### 2) Código e setup

```bash
cd /opt/patient-registration-system
bash linux/setup_linux.sh
```

O setup já faz:
- criação/validação de `.venv`
- instalação de dependências Python
- validação de `SECRET_KEY` e `DATABASE_URL`
- validação de ODBC/`pyodbc`
- `flask db upgrade`
- seed idempotente (`setup_init_data.py`)

### 3) Ajustar `.env` obrigatório

```properties
SECRET_KEY=chave-unica-gerada-para-o-hospital
DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/patient_registration
FLASK_ENV=production
FLASK_DEBUG=0
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DESKTOP_MODE=false
```

### 4) Teste rápido (sem serviço)

```bash
bash linux/run_network.sh
```

Parar com `CTRL+C`.

### 5) Subir em produção com systemd

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

### 6) Publicar na rede via Nginx

```bash
sudo cp linux/nginx/patient-registration.conf /etc/nginx/sites-available/patient-registration
sudo ln -s /etc/nginx/sites-available/patient-registration /etc/nginx/sites-enabled/patient-registration
sudo nginx -t
sudo systemctl reload nginx
```

### 7) Firewall (exemplo UFW)

```bash
sudo ufw allow from 192.168.0.0/16 to any port 80 proto tcp
sudo ufw deny 5000/tcp
```

### 8) Acesso e credenciais iniciais

- URL: `http://IP_DO_SERVIDOR`
- Usuários: `pedro`, `andre`, `brauner`, `savio`, `laecio`
- Senha inicial: `123456`

---

## Problemas comuns

### Porta ocupada
No Linux, ajuste `SERVER_PORT` no `.env` (não usar `FLASK_PORT`).

### Banco não conecta
Verifique `DATABASE_URL` e permissões no PostgreSQL.

### Especialidades não aparecem

```bash
python setup_init_data.py
```

---

## Referências

- [LINUX_DEPLOYMENT.md](./LINUX_DEPLOYMENT.md)
- [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)
- [TROUBLESHOOTING_ESPECIALIDADES.md](./TROUBLESHOOTING_ESPECIALIDADES.md)

**Última atualização**: março/2026
