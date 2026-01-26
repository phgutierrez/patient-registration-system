# 🔨 Guia de Compilação em Windows - v1.0.1

## ⚠️ Importante

Esta aplicação **DEVE SER COMPILADA EM WINDOWS** para gerar os executáveis (.exe).

Compilações em macOS geram aplicativos macOS (.app), não executáveis Windows.

## 📋 Pré-Requisitos

- **Windows 7+** (32 ou 64 bits)
- **Python 3.7+** (testado com 3.13.4)
- **Git** (opcional, apenas para clonar o repositório)

## 🚀 Passos de Compilação

### 1️⃣ Preparar Ambiente

```batch
# Abrir Command Prompt ou PowerShell como Administrador

# Clonar/atualizar repositório
git clone https://github.com/phgutierrez/patient-registration-system.git
cd patient-registration-system
```

### 2️⃣ Instalar Dependências

```batch
# Instalar dependências do projeto
pip install -r requirements.txt

# Verificar instalação
python validate_system.py
```

**Saída esperada:**
```
✓ Python 3.13.4 OK
✓ PyInstaller OK
✓ Waitress OK
... (todos os checks OK)
```

### 3️⃣ Compilar Builds

#### Opção A: Compilação Automática (Recomendado)

```batch
# Executar script de compilação
build_releases.bat
```

Este script irá:
- ✅ Compilar versão 64 bits
- ✅ Compilar versão 32 bits
- ✅ Criar estrutura de diretórios
- ✅ Gerar arquivo release_info.md

#### Opção B: Compilação Manual

```batch
# Build 64 bits
pyinstaller --clean prontuario_64bits.spec

# Build 32 bits
pyinstaller --clean prontuario_32bits.spec
```

**Tempo estimado:** 15-20 minutos por build

### 4️⃣ Verificar Compilação

```batch
# Listar diretórios gerados
dir dist\

# Verificar executáveis
dir dist\64bits\prontuario-64bits\
dir dist\32bits\prontuario-32bits\
```

**Esperado:**
```
dist/
├── 64bits/
│   └── prontuario-64bits/
│       ├── prontuario-64bits.exe
│       ├── ... (outros arquivos)
├── 32bits/
│   └── prontuario-32bits/
│       ├── prontuario-32bits.exe
│       ├── ... (outros arquivos)
└── release_info.md
```

### 5️⃣ Testar Executáveis

```batch
# Testar 64 bits
dist\64bits\prontuario-64bits\prontuario-64bits.exe

# Testar 32 bits
dist\32bits\prontuario-32bits\prontuario-32bits.exe
```

**O aplicativo deve:**
- Iniciar sem erros
- Exibir interface web em http://localhost:5000
- Conectar com sucesso ao banco de dados

### 6️⃣ Criar Arquivos ZIP

```batch
# Comprimir 64 bits
cd dist\64bits
PowerShell -Command "Compress-Archive -Path prontuario-64bits -DestinationPath ..\prontuario-v1.0.1-64bits.zip"

# Comprimir 32 bits
cd ..\32bits
PowerShell -Command "Compress-Archive -Path prontuario-32bits -DestinationPath ..\prontuario-v1.0.1-32bits.zip"

# Verificar ZIPs
cd ..
dir *.zip
```

## 📦 Arquivos Gerados

Após compilação bem-sucedida:

```
dist/
├── prontuario-v1.0.1-64bits.zip  (~50-70 MB)
├── prontuario-v1.0.1-32bits.zip  (~50-70 MB)
└── release_info.md
```

## 🔗 Fazer Upload para GitHub Release

1. Vá para: https://github.com/phgutierrez/patient-registration-system/releases/new
2. Selecione a tag: **v1.0.1**
3. Preencha título e descrição (copiar de RELEASE_v1.0.1.md)
4. Arraste os 2 arquivos .zip para "Attach binaries"
5. Clique em "Publish Release"

## ❓ Troubleshooting

### PyInstaller demora muito ou trava

- Verifique espaço em disco (mínimo 2 GB livre)
- Desabilite antivírus temporariamente
- Execute como Administrador
- Tente `--clean` para limpar cache

### Erro: "prontuario_64bits.spec not found"

- Verifique se está no diretório raiz do projeto
- Execute `dir prontuario_*.spec` para confirmar

### Executável não inicia

- Verifique se todas as dependências foram instaladas
- Rode `python validate_system.py` novamente
- Confira espaço em disco

### ZIP fica muito grande

- Normal ter 50-70 MB (inclui Python runtime)
- Se > 200 MB, pode ter incluído arquivo errado

## ✅ Checklist Final

- [ ] Windows 7 ou superior
- [ ] Python 3.7+ instalado
- [ ] `pip install -r requirements.txt` executado
- [ ] `validate_system.py` passou (todos OK)
- [ ] `build_releases.bat` completou sem erros
- [ ] Executáveis estão em `dist/64bits/` e `dist/32bits/`
- [ ] Executáveis funcionam quando clicados
- [ ] Arquivos ZIP foram criados com sucesso
- [ ] ZIPs podem ser abertos/extraídos

## 📞 Suporte

Se tiver problemas:
1. Consulte [GUIA_COMPILACAO.md](GUIA_COMPILACAO.md) para mais detalhes
2. Verifique [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
3. Confira os logs em `build_*.log` se gerados

---

**Versão:** 1.0.1  
**Data:** 26 de janeiro de 2026  
**Status:** Pronto para compilação Windows
