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

## Credenciais Padrão

**Usuário**: `pedro`
**Senha**: `1234`

(Todos os usuários no setup inicial usam a mesma senha)

## Problemas Comuns

### ❌ "Especialidades não aparecem na tela"
```bash
verify_setup.bat
```
Ver [TROUBLESHOOTING_ESPECIALIDADES.md](./TROUBLESHOOTING_ESPECIALIDADES.md)

### ❌ "Python não encontrado"
Instalar Python 3.11+:
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
FLASK_PORT=5001
```

### ❌ "Erro ao conectar no Google Calendar"
Verificar no arquivo de especialidades (`src/models/calendar_event_status.py`):
```python
# Cada especialidade precisa de agenda_url configurada
```

Ver: [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) - Seção 5.6

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

## Template .env

Se não existir arquivo `.env`, criar com:

```
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=sua-chave-secreta-mudar-isso-aqui-1234567890
DATABASE_URL=sqlite:///instance/prontuario.db
```

## Arquitetura Rápida

```
Cliente (Navegador)
    ↓
Flask Web App (5000)
    ↓
SQLite Database (instance/prontuario.db)
    ↓
Google Calendar API (se configurado)
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

**Última atualização**: v2.5
- ✅ Ordem de migrations corrigida
- ✅ setup_windows.bat reescrito
- ✅ Suporte para especialidades múltiplas
- ✅ verify_setup.bat adicionado
