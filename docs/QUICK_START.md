# Quick Start - Guia Rápido de Instalação e Execução

## Para Instalação (Primeira Vez)

### Windows

```bash
# 1. Abrir Command Prompt ou PowerShell na pasta do projeto
cd C:\seu\caminho\patient-registration-system

# 2. Executar setup
setup_windows.bat

# 3. Esperar até ver: "[OK] SETUP COMPLETADO!"
```

### Verificar se deu certo
```bash
verify_setup.bat
```

Se ver algo como:
```
=== ESPECIALIDADES ===
  - Ortopedia (1) [ATIVADA]
  - Cirurgia Pediatrica (2) [ATIVADA]

Total: 2 especialidade(s)
```

✅ **Tudo OK!**

## Para Executar o Sistema

### Modo Local (Um Computador)
```bash
run_local.bat
```
- Abre em: http://localhost:5000
- Apenas seu computador consegue acessar
- Fecha automaticamente quando fecha o navegador

### Modo Rede (Hospital/Múltiplos Computadores)
```bash
run_network.bat
```
- Abre em: http://seu-ip:5000 (ex: http://192.168.1.50:5000)
- Todos na rede conseguem acessar
- Continua rodando em background até você parar

## Acesso Inicial

1. Abra o arquivo `.env`
2. Preencha `ADMIN_BOOTSTRAP_USERNAME` e `ADMIN_BOOTSTRAP_PASSWORD`
3. Inicie o sistema e faça login com esse usuário
4. O sistema pedirá troca de senha no primeiro acesso

## Problemas Comuns

### ❌ "Especialidades não aparecem na tela"
```bash
verify_setup.bat
```
Ver [TROUBLESHOOTING_ESPECIALIDADES.md](./TROUBLESHOOTING_ESPECIALIDADES.md)

### ❌ "Python não encontrado"
Instalar Python 3.10+:
- Windows: `winget install python`
- Ou baixar de: https://www.python.org/downloads/

### ❌ "Porta 5000 já está em uso"
Se já tiver outra aplicação usando a porta:

#### Opção 1: Encontrar e fechar (recomendado)
```bash
netstat -ano | findstr :5000
REM Ver qual processo, depois fechar no Task Manager
```

#### Opção 2: Usar porta diferente
Editar arquivo `.env` e adicionar:
```
SERVER_PORT=5001
```

### ❌ "Procedimentos/Código SUS não aparecem"
```bash
verify_setup.bat
python setup_init_data.py
```

### ❌ "Erro ao conectar no Google Calendar"
Ver: [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) - Seção 5.6 (agenda por especialidade)

## Próximos Passos

1. **Customizar Especialidades**: [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) - Seção 5.6
2. **Adicionar Usuários**: Usar interface web ou [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) - Seção 6
3. **Integrar com Google Calendar**: [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) - Seção 7

## Arquivos Importantes

| Arquivo | Uso |
|---------|-----|
| `setup_windows.bat` | Instalação inicial (executar UMA VEZ) |
| `run_local.bat` | Rodar no seu computador |
| `run_network.bat` | Rodar na rede do hospital |
| `verify_setup.bat` | Verificar se setup funcionou |
| `.env` | Configurações (criar manualmente, ver exemplo baixo) |

## Template `.env`

Use `.env.example` como base. Exemplo mínimo:

```
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=
SERVER_HOST=127.0.0.1
SERVER_PORT=5000
DESKTOP_MODE=true
ADMIN_BOOTSTRAP_USERNAME=admin.local
ADMIN_BOOTSTRAP_PASSWORD=defina-uma-senha-forte-aqui
```

## Arquitetura Rápida

```
Cliente (Navegador)
    ↓
Flask Web App (5000)
    ↓
SQLite Database (instance/prontuario.db)
    ↓
Google Calendar / feed ICS (se configurado)
```

## Diagrama de Especialidades

```
Página Inicial
    ↓
[Selecionar Especialidade]  ← Carrega de BD
    ↓
[Selecionar Usuário]        ← Filtra por especialidade
    ↓
Dashboard da Especialidade
    ├─ Agenda (Google Calendar específico)
    ├─ Pacientes (dessa especialidade)
    └─ Cirurgias (dessa especialidade)
```

## Suporte

Se tiver problema:

1. Executar: `verify_setup.bat`
2. Copiar output
3. Ver: [TROUBLESHOOTING_ESPECIALIDADES.md](./TROUBLESHOOTING_ESPECIALIDADES.md)
4. Se não resolver, abrir issue em: https://github.com/seu-repo/issues

---

**Última atualização**: v2.6 (março/2026)
- ✅ Seed do EXE alinhado com setup completo
- ✅ Usuários iniciais com especialidade vinculada
- ✅ Procedimentos e código SUS carregados por especialidade
- ✅ Modelos salvos isolados por especialidade + usuário
