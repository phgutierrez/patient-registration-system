# 🚀 Guia Rápido - PatientRegistration.exe

## Como Usar

### 1. Executar o Sistema
```bash
# Opção 1: Duplo clique
dist\PatientRegistration.exe

# Opção 2: Via PowerShell
.\dist\PatientRegistration.exe

# Opção 3: Via batch
.\run_exe.bat
```

### 2. O que Acontece
1. **Executável inicia** → Console abre com mensagens de log
2. **Servidor inicializa** → http://127.0.0.1:5000
3. **Navegador abre automaticamente** → Sistema pronto para uso!
4. **Fazer login** → Selecionar usuário existente ou cadastrar novo

### 3. Encerrar o Sistema
**Opção 1 (Recomendada):**
- Clicar no botão vermelho **"Sair do Sistema"** no menu lateral
- Sistema encerra graciosamente

**Opção 2:**
- Pressionar **CTRL+C** no console
- Sistema encerra imediatamente

## ⚠️ Solução de Problemas

### Problema: Navegador não abre automaticamente
**Solução:** Abra manualmente: http://127.0.0.1:5000

### Problema: Erro "Internal Server Error"
**Causas possíveis:**
1. Banco de dados não inicializado
2. Diretórios faltando
3. Permissões insuficientes

**Soluções:**
1. Execute como Administrador
2. Verifique os logs no console
3. Delete a pasta `instance` e execute novamente

### Problema: Porta 5000 em uso
**Solução:**
```powershell
# Usar porta diferente
$env:PORT=8080
.\dist\PatientRegistration.exe
```

### Problema: Erro ao criar banco de dados
**Solução:**
```powershell
# Deletar banco antigo
Remove-Item -Path "instance\prontuario.db" -Force
# Executar novamente
.\dist\PatientRegistration.exe
```

## 📋 Verificação Rápida

### Teste se está funcionando:
1. Executar PatientRegistration.exe
2. Aguardar mensagem: "Abrindo navegador em http://127.0.0.1:5000"
3. Navegador deve abrir automaticamente
4. Página de login deve aparecer

### Logs Importantes
No console, você verá:
```
============================================================
Patient Registration System
============================================================
Iniciando servidor em http://127.0.0.1:5000
Pressione CTRL+C para parar o servidor
Ou use o botão "Sair do Sistema" na interface
============================================================
Diretório de PDFs verificado: ...
Banco de dados inicializado
Abrindo navegador em http://127.0.0.1:5000
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente
Crie arquivo `.env` na mesma pasta do executável:
```env
HOST=0.0.0.0      # Para acessar de outras máquinas
PORT=5000         # Porta do servidor
SECRET_KEY=chave_secura_aqui
```

### Executar em Rede Local
```powershell
$env:HOST="0.0.0.0"
.\dist\PatientRegistration.exe
```
Acesse de outras máquinas: http://IP_DO_SERVIDOR:5000

## 📊 Estrutura de Dados

Após primeira execução, será criado:
```
patient-registration-system/
├── dist/
│   └── PatientRegistration.exe
├── instance/
│   └── prontuario.db          # Banco de dados SQLite
└── src/
    └── static/
        └── pdfs/
            └── gerados/       # PDFs gerados
```

## 🎯 Primeiro Uso

1. **Executar PatientRegistration.exe**
2. **Cadastrar primeiro usuário:**
   - Clicar em "Cadastro Usuário"
   - Preencher dados
   - Salvar
3. **Fazer login:**
   - Selecionar usuário criado
   - Sistema pronto!

## 💡 Dicas

### Performance
- Primeira execução: ~5-10 segundos (criação do banco)
- Execuções seguintes: ~2-3 segundos
- Fechamento via botão: ~1 segundo

### Backup
Para fazer backup dos dados:
```powershell
Copy-Item "instance\prontuario.db" "backup\prontuario_$(Get-Date -Format 'yyyy-MM-dd').db"
```

### Restaurar Backup
```powershell
Copy-Item "backup\prontuario_2026-01-26.db" "instance\prontuario.db" -Force
```

## 🐛 Debug Mode

Para ver erros detalhados, edite `server.py`:
```python
app.debug = True  # Adicionar antes de serve()
```
Reconstrua o executável com `python build_exe.py`

## 📞 Suporte

### Logs de Erro
Se encontrar problemas, copie os logs do console e salve em arquivo:
```powershell
.\dist\PatientRegistration.exe > logs.txt 2>&1
```

### Informações do Sistema
Para reportar problemas, inclua:
- Windows Version
- Mensagem de erro completa
- Logs do console
- Passos para reproduzir

## ✅ Checklist de Funcionamento

- [ ] Executável inicia sem erros
- [ ] Console mostra mensagens de log
- [ ] Navegador abre automaticamente
- [ ] Página de login aparece
- [ ] Consegue cadastrar usuário
- [ ] Consegue fazer login
- [ ] Consegue cadastrar paciente
- [ ] Botão "Sair do Sistema" funciona

Se todos itens ✓, sistema está OK!
