# ✅ Checklist de Implementação - Build 32bits e 64bits

## 🎯 Fase 1: Preparação Inicial (Uma única vez)

### Instalação do Python 32bits 3.11.9

- [ ] **Baixar Python 32bits**
  - Acesse: https://www.python.org/downloads/release/python-3119/
  - Procure por: "Windows installer (32-bit)"
  - Arquivo: python-3.11.9.exe (versão 32bits)

- [ ] **Instalar Python 32bits**
  - Execute como administrador
  - NÃO marque "Add Python to PATH"
  - Anote o caminho (ex: C:\Python311_32)
  - Verifique: `C:\Python311_32\python.exe --version`

### Configuração do Ambiente Virtual 32bits

- [ ] **Criar pasta do projeto se ainda não existir**
  ```powershell
  cd "D:\Users\phgut\OneDrive\Documentos\patient-registration-system"
  ```

- [ ] **Criar ambiente virtual 32bits**
  ```powershell
  C:\Python311_32\python.exe -m venv .venv32
  ```

- [ ] **Ativar ambiente virtual**
  ```powershell
  .\.venv32\Scripts\Activate.ps1
  ```

- [ ] **Atualizar pip**
  ```powershell
  python -m pip install --upgrade pip
  ```

- [ ] **Instalar dependências do projeto**
  ```powershell
  pip install -r requirements.txt
  ```

- [ ] **Instalar ferramentas de build**
  ```powershell
  pip install PyInstaller==6.1.0
  pip install waitress
  ```

- [ ] **Verificar instalação**
  ```powershell
  pip list
  # Deve listar: PyInstaller, waitress, flask, etc.
  ```

---

## 🔄 Fase 2: Validação de Arquivos Criados

### Verificar Arquivos Modificados

- [ ] **build_exe.py**
  - Contém: `'--distpath=dist/Sistema64bits',`
  - Executável será gerado em `dist/Sistema64bits/PatientRegistration/`

- [ ] **create-release.ps1**
  - Contém: `$Python32bitPath = ...`
  - Fluxo expandido para 9 passos
  - Compacta ambos os sistemas em um ZIP

### Verificar Novos Arquivos

- [ ] **build_exe_32bits.py** existe e contém:
  - `'--distpath=dist/Sistema32bits',`
  - Saída em `dist/Sistema32bits/PatientRegistration/`

- [ ] **PatientRegistration_32bits.spec** existe e é válido

- [ ] **PYTHON_32BITS_SETUP.md** contém documentação completa

---

## 🧪 Fase 3: Testes Individuais

### Teste do Build 64bits

- [ ] **Ativar ambiente 64bits padrão**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

- [ ] **Executar build 64bits**
  ```powershell
  python build_exe.py
  ```

- [ ] **Verificar resultado**
  - [ ] Pasta `dist/Sistema64bits/` foi criada
  - [ ] Arquivo `dist/Sistema64bits/PatientRegistration/PatientRegistration.exe` existe
  - [ ] Tamanho é razoável (300-400 MB)

### Teste do Build 32bits

- [ ] **Desativar ambiente 64bits** (opcional)
  ```powershell
  deactivate
  ```

- [ ] **Ativar ambiente 32bits**
  ```powershell
  .\.venv32\Scripts\Activate.ps1
  ```

- [ ] **Executar build 32bits**
  ```powershell
  python build_exe_32bits.py
  ```

- [ ] **Verificar resultado**
  - [ ] Pasta `dist/Sistema32bits/` foi criada
  - [ ] Arquivo `dist/Sistema32bits/PatientRegistration/PatientRegistration.exe` existe
  - [ ] Tamanho é razoável (300-400 MB)

---

## 🚀 Fase 4: Teste de Release Completa

### Preparar Release

- [ ] **Desativar ambientes virtuais**
  ```powershell
  deactivate
  ```

- [ ] **Executar script de release**
  ```powershell
  .\create-release.ps1 -Version "1.0.0" -Message "Suporte a 32 e 64 bits"
  ```

- [ ] **Acompanhar progresso no console**
  - [ ] Passo 1-2: Limpeza concluída
  - [ ] Passo 3-4: Build 64bits concluído
  - [ ] Passo 5-6: Build 32bits concluído (ou aviso se Python 32bits não estiver configurado)
  - [ ] Passo 7: ZIP criado
  - [ ] Passo 8-9: Commit e tag criados

### Validar Resultado Final

- [ ] **ZIP foi criado**
  - Arquivo: `PatientRegistration-v1.0.0-windows.zip`
  - Tamanho: 600-800 MB (aproximadamente)

- [ ] **Conteúdo do ZIP**
  - [ ] Contém `PatientRegistration/` (64bits)
  - [ ] Contém `PatientRegistration/` (32bits)
  - [ ] Ambos têm pasta `_internal/`

- [ ] **Git foi atualizado**
  - [ ] Tag `v1.0.0` foi criada
  - [ ] Commit foi feito
  - [ ] Push para `origin master` foi realizado
  - [ ] Tag foi enviada para GitHub

---

## 🐛 Fase 5: Troubleshooting (Se Necessário)

### Erro: "Python 32bits não encontrado"

- [ ] Verificar instalação: `C:\Python311_32\python.exe --version`
- [ ] Editar `create-release.ps1` e corrigir `$Python32bitPath`
- [ ] Re-executar script de release

### Erro ao Ativar Ambiente Virtual 32bits

- [ ] Verificar se PowerShell tem permissão:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- [ ] Tentar novamente: `.\.venv32\Scripts\Activate.ps1`

### PyInstaller falha no build 32bits

- [ ] Verificar instalação do PyInstaller:
  ```powershell
  .\.venv32\Scripts\Activate.ps1
  pip install PyInstaller==6.1.0 --force-reinstall
  ```
- [ ] Limpar caches:
  ```powershell
  Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
  ```
- [ ] Re-executar build: `python build_exe_32bits.py`

### Executável 32bits não inicia

- [ ] Verificar se todas as dependências foram instaladas:
  ```powershell
  .\.venv32\Scripts\Activate.ps1
  pip list
  ```
- [ ] Testar em máquina 32bits se possível
- [ ] Verificar logs na pasta `dist\Sistema32bits\PatientRegistration\`

### ZIP não contém ambos os sistemas

- [ ] Verificar se Python 32bits foi configurado corretamente
- [ ] Executar manualmente:
  ```powershell
  Compress-Archive -Path "dist\Sistema64bits\PatientRegistration" -DestinationPath "PatientRegistration-v1.0.0-windows.zip" -Force
  Compress-Archive -Path "dist\Sistema32bits\PatientRegistration" -DestinationPath "PatientRegistration-v1.0.0-windows.zip" -Update
  ```

---

## 📋 Fase 6: Validação Final

### Testes de Funcionalidade

- [ ] **Teste 64bits em máquina 64bits**
  - [ ] Executável inicia sem erros
  - [ ] Aplicação Flask funciona normalmente
  - [ ] Banco de dados é acessado corretamente
  - [ ] PDFs são gerados sem problemas

- [ ] **Teste 32bits em máquina 32bits (se possível)**
  - [ ] Executável inicia sem erros
  - [ ] Aplicação Flask funciona normalmente
  - [ ] Banco de dados é acessado corretamente
  - [ ] PDFs são gerados sem problemas

### Testes de Release

- [ ] **Arquivo ZIP foi enviado para GitHub**
  - Acesse: https://github.com/phgutierrez/patient-registration-system/releases

- [ ] **Tag foi criada corretamente**
  - Nome: `v1.0.0`
  - Mensagem: "Suporte a 32 e 64 bits"

- [ ] **ZIP pode ser baixado do GitHub**
  - [ ] Download funciona
  - [ ] Arquivo pode ser extraído
  - [ ] Ambos os executáveis estão presentes

---

## 📝 Documentação

- [ ] **PYTHON_32BITS_SETUP.md**
  - [ ] Revisado e atualizado
  - [ ] Todas as instruções são claras
  - [ ] Passos foram testados

- [ ] **BUILD_32BITS_RESUMO.md**
  - [ ] Contém resumo das alterações
  - [ ] Lista arquivos modificados
  - [ ] Inclui checklist de implementação

- [ ] **Este arquivo (CHECKLIST)**
  - [ ] Todos os itens foram completados
  - [ ] Assinados e datados

---

## ✨ Resumo Final

**Data de Conclusão:** ___/___/_____

**Responsável:** _____________________________

**Status Geral:** 
- [ ] ✅ Todos os itens completados
- [ ] ⚠️ Alguns itens pendentes (listar abaixo)
- [ ] ❌ Itens críticos faltando

**Itens Pendentes (se houver):**
1. _________________________________
2. _________________________________
3. _________________________________

**Observações:**
___________________________________________________________________
___________________________________________________________________
___________________________________________________________________

---

**Próximos Passos Recomendados:**
1. Monitorar builds e releases futuras
2. Coletar feedback de usuários 32bits
3. Atualizar documentação conforme necessário
4. Manter ambientes Python atualizados

**Contato para Dúvidas:** Consulte PYTHON_32BITS_SETUP.md ou BUILD_32BITS_RESUMO.md
