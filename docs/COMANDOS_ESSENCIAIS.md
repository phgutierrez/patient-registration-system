# ⚡ Comandos Essenciais (Windows)

Referência rápida para setup, execução, migração e build do executável.

---

## 1) Setup inicial

```powershell
# Na raiz do projeto
cd C:\caminho\patient-registration-system

# Setup completo (venv + dependências + banco + dados iniciais)
.\setup_windows.bat

# Verificação pós-setup
.\verify_setup.bat
```

Credenciais padrão criadas no setup:
- Usuários: `pedro`, `andre`, `brauner`, `savio`, `laecio`
- Senha: `123456`

---

## 2) Executar aplicação

```powershell
# Modo local (somente este PC)
.\run_local.bat

# Modo rede LAN (acesso de outros PCs)
.\run_network.bat
```

---

## 3) Ambiente virtual manual (opcional)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4) Migrações Alembic

```powershell
# Aplicar todas as migrações
alembic upgrade head

# Ver histórico
alembic history

# Ver migração atual
alembic current

# Criar nova migração (quando necessário)
alembic revision -m "descricao_da_migracao"
```

---

## 5) Build do executável (32 bits)

```powershell
# Com ambiente ativo e dependências instaladas
python .\build_exe_32bits.py
```

Saída esperada:
- Executável em `dist\Sistema32bits\PatientRegistration\PatientRegistration.exe`

---

## 6) Troubleshooting rápido

```powershell
# Verificar Python
python --version

# Verificar dependências
pip check

# Reinstalar dependências
pip install -r requirements.txt --upgrade

# Recriar banco local (CUIDADO: apaga dados)
del .\instance\prontuario.db
.\setup_windows.bat
```

Porta 5000 em uso:

```powershell
netstat -ano | findstr :5000
```

Especialidades/procedimentos não aparecem:

```powershell
.\verify_setup.bat
python .\setup_init_data.py
```

---

## 7) Comandos úteis no desenvolvimento

```powershell
# Rodar app direto em Python
python run.py

# Rodar servidor de produção local
python server.py

# Atualizar schema (utilitário do projeto)
python update_db.py
```

---

Última atualização: março/2026 (v2.6)

