# Guia de Configuração - Python 32bits 3.11.9 e Build Sistema32bits

## 📋 Visão Geral

Este guia detalha o processo de instalação e configuração do Python 32bits (3.11.9) necessário para gerar o executável de 32 bits do Sistema de Registro de Pacientes.

## 🛠️ Requisitos

- Windows 10 ou superior (com suporte a aplicações 32 bits)
- Acesso de administrador na máquina
- Python 32bits versão 3.11.9
- Ambiente virtual separado (`.venv32`) para evitar conflitos com a instalação de 64 bits

## 📥 Passo 1: Instalação do Python 32bits 3.11.9

### 1.1 Download

1. Acesse: https://www.python.org/downloads/release/python-3119/
2. Procure por "Windows installer (32-bit)"
3. Baixe o arquivo `python-3.11.9-amd64.exe` (NÃO é o 64-bit, o nome é enganoso)

**IMPORTANTE:** Certifique-se de baixar a versão 32bits!

### 1.2 Instalação

1. Execute o instalador como administrador
2. **NÃO marque** "Add Python 3.11 to PATH" (para evitar conflitos com a instalação 64bits)
3. Escolha "Install Now" ou customize os componentes:
   - ✓ pip
   - ✓ py launcher
   - ✓ tcl/tk
4. Anote o caminho de instalação (ex: `C:\Python311_32`)

### 1.3 Verificação

Abra o PowerShell e execute:

```powershell
# Verificar a instalação (substitua pelo caminho correto)
C:\Python311_32\python.exe --version

# Deve exibir:
# Python 3.11.9
```

## 🔧 Passo 2: Configuração do Ambiente Virtual 32bits

Navegue até a pasta do projeto:

```powershell
cd "D:\Users\phgut\OneDrive\Documentos\patient-registration-system"
```

### 2.1 Criação do Ambiente Virtual

```powershell
# Criar ambiente virtual com Python 32bits
C:\Python311_32\python.exe -m venv .venv32

# Ativar o ambiente virtual
.\.venv32\Scripts\Activate.ps1
```

**Se receber erro de execução**, execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2.2 Instalação de Dependências

Com o ambiente virtual ativado (`.venv32`):

```powershell
# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências do projeto
pip install -r requirements.txt

# Instalar ferramentas adicionais para build
pip install PyInstaller==6.1.0
pip install waitress

# Verificar instalação
pip list
```

## 🏗️ Passo 3: Build do Executável 32bits

Com o ambiente virtual 32bits ativado:

```powershell
# No PowerShell, na pasta do projeto
python build_exe_32bits.py
```

### Resultado esperado:

- Pasta criada: `dist\Sistema32bits\PatientRegistration`
- Arquivo: `dist\Sistema32bits\PatientRegistration\PatientRegistration.exe`
- Tamanho aproximado: 300-400 MB

## 📦 Passo 4: Atualizar Script de Release

O arquivo `create-release.ps1` foi atualizado para detectar automaticamente o ambiente Python 32bits:

```powershell
$Python32bitPath = "D:/Users/phgut/OneDrive/Documentos/patient-registration-system/.venv32/Scripts/python.exe"
```

**Se o caminho for diferente, edite o arquivo `create-release.ps1` e ajuste a variável `$Python32bitPath`.**

## 🚀 Passo 5: Criar Release Completa

Com ambos os ambientes configurados (64bits e 32bits), execute:

```powershell
# Criar release da versão 1.0.0
.\create-release.ps1 -Version "1.0.0" -Message "Suporte a sistemas 32 e 64 bits"
```

O script irá:

1. ✅ Limpar builds anteriores
2. ✅ Criar executável 64bits em `dist\Sistema64bits`
3. ✅ Criar executável 32bits em `dist\Sistema32bits`
4. ✅ Compactar ambos em um único ZIP
5. ✅ Criar commit e tag no Git
6. ✅ Enviar para o GitHub

## 🔍 Troubleshooting

### Erro: "Python 32bits não encontrado"

- Verifique se Python 32bits está instalado: `C:\Python311_32\python.exe --version`
- Confirme o caminho em `create-release.ps1` na variável `$Python32bitPath`

### Erro: "pip não encontrado no .venv32"

```powershell
# Recriar ambiente virtual
.\.venv32\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### PyInstaller não funciona

```powershell
# Certifique-se que está ativado o .venv32
.\.venv32\Scripts\Activate.ps1

# Reinstale PyInstaller
pip uninstall PyInstaller
pip install PyInstaller==6.1.0
```

### Executável 32bits não inicia

1. Verifique se todas as dependências foram instaladas: `pip list`
2. Teste em uma máquina 32bits
3. Verifique os logs em `dist\Sistema32bits\PatientRegistration\logs`

## 📊 Estrutura de Saída

Após executar `.\create-release.ps1 -Version "1.0.0"`:

```
dist/
├── Sistema64bits/
│   └── PatientRegistration/
│       ├── PatientRegistration.exe (executável 64bits)
│       ├── _internal/ (dependências)
│       └── ... (outros arquivos)
│
└── Sistema32bits/
    └── PatientRegistration/
        ├── PatientRegistration.exe (executável 32bits)
        ├── _internal/ (dependências)
        └── ... (outros arquivos)

PatientRegistration-v1.0.0-windows.zip
├── PatientRegistration/ (64bits)
└── PatientRegistration/ (32bits)
```

## 🎯 Resumo de Comandos Importantes

```powershell
# Ativar ambiente 64bits
.\.venv\Scripts\Activate.ps1

# Ativar ambiente 32bits
.\.venv32\Scripts\Activate.ps1

# Build 64bits
python build_exe.py

# Build 32bits (com ambiente 32bits ativado)
python build_exe_32bits.py

# Release completa (ambos os sistemas)
.\create-release.ps1 -Version "X.Y.Z"
```

## 🔗 Referências

- Python Download: https://www.python.org/downloads/
- PyInstaller Documentation: https://pyinstaller.org/
- Waitress Server: https://docs.pylonsproject.org/projects/waitress/

---

**Última atualização:** 26 de janeiro de 2026

**Versão:** 1.0.0

**Ambiente:** Windows 10+ com Python 3.11.9 (32bits e 64bits)
