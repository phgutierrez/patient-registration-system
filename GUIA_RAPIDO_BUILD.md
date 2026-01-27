# 🚀 Guia Rápido - Build 32bits e 64bits

## ⚡ Comandos Essenciais

### Primeira Execução (Setup)

```powershell
# 1. Instalar Python 32bits 3.11.9
# (Baixe de https://www.python.org/downloads/release/python-3119/)
# (Ver PYTHON_32BITS_SETUP.md para instruções detalhadas)

# 2. Criar ambiente virtual 32bits
C:\Python311_32\python.exe -m venv .venv32

# 3. Ativar e configurar
.\.venv32\Scripts\Activate.ps1
pip install -r requirements.txt
pip install PyInstaller==6.1.0 waitress
```

---

## 📦 Build Individual

### Build 64bits (Python 64bits padrão)

```powershell
# Ativar ambiente 64bits
.\.venv\Scripts\Activate.ps1

# Executar build
python build_exe.py

# Resultado: dist\Sistema64bits\PatientRegistration\PatientRegistration.exe
```

### Build 32bits (Python 32bits)

```powershell
# Ativar ambiente 32bits
.\.venv32\Scripts\Activate.ps1

# Executar build
python build_exe_32bits.py

# Resultado: dist\Sistema32bits\PatientRegistration\PatientRegistration.exe
```

---

## 🎯 Release Completa

```powershell
# Criar release (ambas as arquiteturas)
.\create-release.ps1 -Version "1.0.0"

# Ou com mensagem personalizada
.\create-release.ps1 -Version "1.0.0" -Message "Melhorias gerais"
```

**O script irá automaticamente:**
1. ✅ Construir 64bits
2. ✅ Construir 32bits
3. ✅ Compactar ambos em ZIP
4. ✅ Criar commit no Git
5. ✅ Criar e enviar tag

---

## 📁 Estrutura de Pastas

```
dist/
├── Sistema64bits/
│   └── PatientRegistration/
│       └── PatientRegistration.exe
│
└── Sistema32bits/
    └── PatientRegistration/
        └── PatientRegistration.exe

PatientRegistration-v1.0.0-windows.zip
├── PatientRegistration/ (64bits)
└── PatientRegistration/ (32bits)
```

---

## 🔍 Verificação

### Testar Executável 64bits
```powershell
# Iniciar aplicação
.\dist\Sistema64bits\PatientRegistration\PatientRegistration.exe

# Acessar: http://localhost:8080 (ou porta configurada)
```

### Testar Executável 32bits
```powershell
# Iniciar aplicação
.\dist\Sistema32bits\PatientRegistration\PatientRegistration.exe

# Acessar: http://localhost:8080 (ou porta configurada)
```

---

## 🐛 Problemas Comuns

| Problema | Solução |
|----------|---------|
| "Python 32bits não encontrado" | Instalar Python 32bits 3.11.9 (ver PYTHON_32BITS_SETUP.md) |
| ".venv32 não existe" | `C:\Python311_32\python.exe -m venv .venv32` |
| PyInstaller não encontrado | `pip install PyInstaller==6.1.0` |
| Executável não inicia | Verificar pasta `_internal/` e logs |
| ZIP incompleto | Executar ambos os builds antes de fazer release |

---

## 📖 Documentação Completa

- **PYTHON_32BITS_SETUP.md** → Instalação detalhada de Python 32bits
- **BUILD_32BITS_RESUMO.md** → Resumo das alterações realizadas
- **CHECKLIST_IMPLEMENTACAO.md** → Checklist fase-a-fase

---

## ✨ Resumo

| Item | 64bits | 32bits |
|------|--------|--------|
| Script de Build | `build_exe.py` | `build_exe_32bits.py` |
| Spec File | `PatientRegistration.spec` | `PatientRegistration_32bits.spec` |
| Saída | `dist/Sistema64bits/` | `dist/Sistema32bits/` |
| Python | 3.11.9 (64bits) | 3.11.9 (32bits) |
| Ambiente | `.venv` | `.venv32` |

---

## 🎯 Fluxo Completo em 3 Passos

```powershell
# PASSO 1: Setup inicial (uma única vez)
C:\Python311_32\python.exe -m venv .venv32
.\.venv32\Scripts\Activate.ps1
pip install -r requirements.txt
pip install PyInstaller==6.1.0 waitress

# PASSO 2: Build individual (quando necessário)
.\.venv\Scripts\Activate.ps1
python build_exe.py

.\.venv32\Scripts\Activate.ps1
python build_exe_32bits.py

# PASSO 3: Release completa (versões finais)
.\create-release.ps1 -Version "1.0.0"
```

---

**Precisa de ajuda?** Consulte:
- PYTHON_32BITS_SETUP.md (instalação e configuração)
- BUILD_32BITS_RESUMO.md (visão geral das mudanças)
- CHECKLIST_IMPLEMENTACAO.md (passo-a-passo detalhado)
