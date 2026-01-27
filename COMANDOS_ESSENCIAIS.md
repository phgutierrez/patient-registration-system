# ⚡ COMANDOS ESSENCIAIS - Copiar e Colar

## 🎯 Guia para Copiar e Executar

Todos os comandos necessários para setup, build e release em um único arquivo de referência.

---

## 📋 FASE 1: SETUP INICIAL (primeira vez)

### 1.1 - Instalar Python 32bits
```
Acesse: https://www.python.org/downloads/release/python-3119/
Procure por: Windows installer (32-bit)
Baixe e execute como administrador
Não marque "Add Python to PATH"
```

### 1.2 - Criar Ambiente Virtual 32bits
```powershell
C:\Python311_32\python.exe -m venv .venv32
```

### 1.3 - Ativar Ambiente 32bits
```powershell
.\.venv32\Scripts\Activate.ps1
```

### 1.4 - Permitir Execução de Scripts
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 1.5 - Atualizar pip
```powershell
python -m pip install --upgrade pip
```

### 1.6 - Instalar Dependências
```powershell
pip install -r requirements.txt
```

### 1.7 - Instalar Ferramentas de Build
```powershell
pip install PyInstaller==6.1.0
pip install waitress
```

### 1.8 - Verificar Instalação
```powershell
pip list
```

---

## 🔨 FASE 2: BUILD INDIVIDUAL

### 2.1 - Build 64bits (Padrão)
```powershell
.\.venv\Scripts\Activate.ps1
python build_exe.py
```

**Resultado esperado:**
```
dist\Sistema64bits\PatientRegistration\PatientRegistration.exe
```

### 2.2 - Build 32bits
```powershell
.\.venv32\Scripts\Activate.ps1
python build_exe_32bits.py
```

**Resultado esperado:**
```
dist\Sistema32bits\PatientRegistration\PatientRegistration.exe
```

### 2.3 - Testar Executável 64bits
```powershell
.\dist\Sistema64bits\PatientRegistration\PatientRegistration.exe
```

### 2.4 - Testar Executável 32bits
```powershell
.\dist\Sistema32bits\PatientRegistration\PatientRegistration.exe
```

---

## 📦 FASE 3: RELEASE COMPLETA

### 3.1 - Release Versão 1.0.0
```powershell
.\create-release.ps1 -Version "1.0.0"
```

### 3.2 - Release com Mensagem Personalizada
```powershell
.\create-release.ps1 -Version "1.0.0" -Message "Suporte a 32 e 64 bits"
```

### 3.3 - Release Versão 1.1.0
```powershell
.\create-release.ps1 -Version "1.1.0"
```

### 3.4 - Release Versão 2.0.0 com Descrição
```powershell
.\create-release.ps1 -Version "2.0.0" -Message "Lançamento principal com novos recursos"
```

---

## 🧪 VALIDAÇÃO E TESTES

### 4.1 - Verificar Tamanho do Executável 64bits
```powershell
(Get-Item "dist\Sistema64bits\PatientRegistration\PatientRegistration.exe").Length / 1MB
```

### 4.2 - Verificar Tamanho do Executável 32bits
```powershell
(Get-Item "dist\Sistema32bits\PatientRegistration\PatientRegistration.exe").Length / 1MB
```

### 4.3 - Verificar Tamanho do ZIP
```powershell
(Get-Item "PatientRegistration-v1.0.0-windows.zip").Length / 1MB
```

### 4.4 - Listar Conteúdo do ZIP
```powershell
Expand-Archive "PatientRegistration-v1.0.0-windows.zip" -DestinationPath "temp_extract"
Get-ChildItem "temp_extract" -Recurse
Remove-Item "temp_extract" -Recurse
```

### 4.5 - Verificar Integridade do Python 32bits
```powershell
C:\Python311_32\python.exe --version
```

### 4.6 - Verificar Ambiente Virtual 32bits
```powershell
.\.venv32\Scripts\Activate.ps1
python --version
pip list | Select-Object -First 5
deactivate
```

---

## 🧹 LIMPEZA E MANUTENÇÃO

### 5.1 - Limpar Pasta dist
```powershell
Remove-Item -Recurse -Force "dist"
```

### 5.2 - Limpar Pasta build
```powershell
Remove-Item -Recurse -Force "build"
```

### 5.3 - Remover Arquivos .pyc
```powershell
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
```

### 5.4 - Remover __pycache__
```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
```

### 5.5 - Limpar Ambiente Virtual 32bits (CUIDADO!)
```powershell
Remove-Item -Recurse -Force ".venv32"
```

### 5.6 - Limpar Tudo (Reconstruir do Zero)
```powershell
Remove-Item -Recurse -Force "dist"
Remove-Item -Recurse -Force "build"
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
```

---

## 🔧 TROUBLESHOOTING RÁPIDO

### 6.1 - Verificar Python 64bits
```powershell
.\.venv\Scripts\Activate.ps1
python --version
deactivate
```

### 6.2 - Verificar Python 32bits
```powershell
C:\Python311_32\python.exe --version
```

### 6.3 - Reinstalar PyInstaller 64bits
```powershell
.\.venv\Scripts\Activate.ps1
pip uninstall PyInstaller -y
pip install PyInstaller==6.1.0
deactivate
```

### 6.4 - Reinstalar PyInstaller 32bits
```powershell
.\.venv32\Scripts\Activate.ps1
pip uninstall PyInstaller -y
pip install PyInstaller==6.1.0
deactivate
```

### 6.5 - Recriar Ambiente Virtual 32bits
```powershell
Remove-Item -Recurse -Force ".venv32"
C:\Python311_32\python.exe -m venv .venv32
.\.venv32\Scripts\Activate.ps1
pip install -r requirements.txt
pip install PyInstaller==6.1.0 waitress
```

### 6.6 - Verificar Caminho do Python 32bits
```powershell
Get-Item "C:\Python311_32\python.exe"
```

### 6.7 - Listar Ambientes Virtuais
```powershell
Get-ChildItem -Directory | Where-Object {$_.Name -like ".venv*"}
```

---

## 📖 REFERÊNCIA DOCUMENTAÇÃO

### Leitura Recomendada (em ordem)
```
1. 00_COMECE_AQUI.md
2. IMPLEMENTACAO_CONCLUIDA.md
3. GUIA_RAPIDO_BUILD.md
4. PYTHON_32BITS_SETUP.md
5. CHECKLIST_IMPLEMENTACAO.md
```

### Consulta Rápida
```
- GUIA_RAPIDO_BUILD.md (comandos)
- RESUMO_VISUAL.md (diagramas)
- BUILD_32BITS_RESUMO.md (detalhes)
- INDICE_COMPLETO.md (índice)
```

---

## 🎯 FLUXO COMPLETO EM COMANDOS

### Setup (Primeira vez)
```powershell
# 1. Instalar Python 32bits (manual, via navegador)
# 2. Criar .venv32
C:\Python311_32\python.exe -m venv .venv32

# 3. Ativar
.\.venv32\Scripts\Activate.ps1

# 4. Instalar
pip install -r requirements.txt
pip install PyInstaller==6.1.0 waitress

# 5. Desativar
deactivate
```

### Build 64bits
```powershell
.\.venv\Scripts\Activate.ps1
python build_exe.py
deactivate
```

### Build 32bits
```powershell
.\.venv32\Scripts\Activate.ps1
python build_exe_32bits.py
deactivate
```

### Release Completa
```powershell
.\create-release.ps1 -Version "1.0.0"
```

---

## ✅ CHECKLIST DE EXECUÇÃO

```
□ Python 32bits instalado?
  Teste: C:\Python311_32\python.exe --version

□ .venv32 criado?
  Teste: Test-Path ".venv32"

□ Dependências instaladas?
  Teste: .\.venv32\Scripts\Activate.ps1; pip list

□ Build 64bits funciona?
  Teste: .\.venv\Scripts\Activate.ps1; python build_exe.py

□ Build 32bits funciona?
  Teste: .\.venv32\Scripts\Activate.ps1; python build_exe_32bits.py

□ Release completa funciona?
  Teste: .\create-release.ps1 -Version "1.0.0"

□ ZIP contém ambas as versões?
  Teste: Expand-Archive "PatientRegistration-v1.0.0-windows.zip"

□ Executáveis foram criados?
  Teste: Test-Path "dist\Sistema64bits\*" ; Test-Path "dist\Sistema32bits\*"
```

---

## 🚨 ERROS COMUNS E SOLUÇÕES

### "Python 32bits não encontrado"
```powershell
# Solução: Instalar Python 32bits conforme documentação
# OU ajustar caminho em create-release.ps1
```

### ".venv32 não existe"
```powershell
# Solução:
C:\Python311_32\python.exe -m venv .venv32
```

### "PyInstaller não encontrado"
```powershell
# Solução:
.\.venv32\Scripts\Activate.ps1
pip install PyInstaller==6.1.0
```

### "Executável não inicia"
```powershell
# Verifique:
Test-Path "dist\Sistema64bits\PatientRegistration\PatientRegistration.exe"
Test-Path "dist\Sistema32bits\PatientRegistration\PatientRegistration.exe"
# Se não existir, refaça o build
```

### "ZIP não contém ambas as versões"
```powershell
# Verifique se ambos os builds foram criados:
Test-Path "dist\Sistema64bits"
Test-Path "dist\Sistema32bits"
# Se não, execute ambos os builds antes de fazer release
```

---

## 📱 RÁPIDO E FÁCIL

### 3 linhas para setup
```powershell
C:\Python311_32\python.exe -m venv .venv32
.\.venv32\Scripts\Activate.ps1
pip install -r requirements.txt; pip install PyInstaller==6.1.0 waitress
```

### 3 linhas para build
```powershell
.\.venv\Scripts\Activate.ps1; python build_exe.py
.\.venv32\Scripts\Activate.ps1; python build_exe_32bits.py
deactivate
```

### 1 linha para release
```powershell
.\create-release.ps1 -Version "1.0.0"
```

---

**Salve este arquivo como favorito para referência rápida!**

📍 Arquivo: `COMANDOS_ESSENCIAIS.md`  
📅 Data: 26 de janeiro de 2026  
✅ Status: Pronto para cópiar e colar
