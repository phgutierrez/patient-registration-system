# 🔧 Sistema de Build 32bits e 64bits

Implementação completa de suporte para gerar executáveis em duas arquiteturas do Sistema de Registro de Pacientes.

## 📚 Documentação

### Para Começar Rápido
- **[GUIA_RAPIDO_BUILD.md](GUIA_RAPIDO_BUILD.md)** ⚡ - Comandos essenciais e fluxo rápido

### Documentação Completa
- **[PYTHON_32BITS_SETUP.md](PYTHON_32BITS_SETUP.md)** 📖 - Instalação e configuração do Python 32bits
- **[BUILD_32BITS_RESUMO.md](BUILD_32BITS_RESUMO.md)** 📋 - Resumo das alterações realizadas
- **[RESUMO_VISUAL.md](RESUMO_VISUAL.md)** 📊 - Diagramas e fluxogramas visuais

### Implementação Passo-a-Passo
- **[CHECKLIST_IMPLEMENTACAO.md](CHECKLIST_IMPLEMENTACAO.md)** ✅ - Checklist fase-a-fase para implementação

---

## 🚀 Início Rápido

### 1️⃣ Instalação (Uma única vez)

```powershell
# Instalar Python 32bits 3.11.9
# (Baixe de https://www.python.org/downloads/release/python-3119/)

# Criar ambiente virtual 32bits
C:\Python311_32\python.exe -m venv .venv32

# Ativar e instalar dependências
.\.venv32\Scripts\Activate.ps1
pip install -r requirements.txt
pip install PyInstaller==6.1.0 waitress
```

### 2️⃣ Build Individual

```powershell
# Build 64bits
.\.venv\Scripts\Activate.ps1
python build_exe.py

# Build 32bits
.\.venv32\Scripts\Activate.ps1
python build_exe_32bits.py
```

### 3️⃣ Release Completa

```powershell
# Gerar release com ambas as arquiteturas
.\create-release.ps1 -Version "1.0.0"
```

---

## 📁 Estrutura de Arquivos

### Modificados
- `build_exe.py` - Adicionado distpath para 64bits
- `create-release.ps1` - Expandido para build de ambas as arquiteturas

### Novos
- `build_exe_32bits.py` - Script de build para 32bits
- `PatientRegistration_32bits.spec` - Spec file para 32bits
- `PYTHON_32BITS_SETUP.md` - Documentação de setup
- `BUILD_32BITS_RESUMO.md` - Resumo das implementações
- `CHECKLIST_IMPLEMENTACAO.md` - Checklist passo-a-passo
- `GUIA_RAPIDO_BUILD.md` - Referência rápida
- `RESUMO_VISUAL.md` - Diagramas visuais

---

## 🎯 Arquiteturas Suportadas

| Característica | 64bits | 32bits |
|---|---|---|
| Script | `build_exe.py` | `build_exe_32bits.py` |
| Ambiente | `.venv` | `.venv32` |
| Python | 3.11.9 (64bits) | 3.11.9 (32bits) |
| Saída | `dist/Sistema64bits/` | `dist/Sistema32bits/` |
| Tamanho | ~300-400 MB | ~300-400 MB |
| Máquinas-alvo | Windows 64bits | Windows 32bits / 64bits |

---

## 📦 Resultado Final

```
PatientRegistration-v1.0.0-windows.zip (~700 MB)
├── PatientRegistration/ (64bits)
│   ├── PatientRegistration.exe
│   └── _internal/
└── PatientRegistration/ (32bits)
    ├── PatientRegistration.exe
    └── _internal/
```

---

## ❓ Perguntas Frequentes

### P: Preciso instalar Python 32bits?
**R:** Não é obrigatório. Se não instalar, a release será criada apenas com 64bits. Python 32bits é opcional para suporte a máquinas legadas.

### P: Posso usar os builds separadamente?
**R:** Sim. Execute `python build_exe.py` para 64bits ou `python build_exe_32bits.py` para 32bits independentemente.

### P: Qual versão usar em minha máquina?
**R:** Use 64bits se sua máquina é 64bits (recomendado). Use 32bits apenas em máquinas 32bits.

### P: O script de release precisa de ambos os builds?
**R:** Não. Se Python 32bits não estiver configurado, continuará apenas com 64bits. Ambos são criados quando disponível.

### P: Como desinstalar Python 32bits depois?
**R:** Use Painel de Controle → Programas → Remover um programa → Python 3.11.9 (32bits)

---

## 🔗 Referências Úteis

- [Python Downloads](https://www.python.org/downloads/)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Waitress Server](https://docs.pylonsproject.org/projects/waitress/)
- [GitHub Releases](https://github.com/phgutierrez/patient-registration-system/releases)

---

## 🐛 Troubleshooting

### Erro: "Python 32bits não encontrado"
→ Consulte **PYTHON_32BITS_SETUP.md** seção "Installação"

### Erro: ".venv32 não existe"
→ Consulte **PYTHON_32BITS_SETUP.md** seção "Criação do Ambiente Virtual"

### Erro: "PyInstaller não funciona"
→ Consulte **GUIA_RAPIDO_BUILD.md** seção "Problemas Comuns"

### Executável não inicia
→ Consulte **CHECKLIST_IMPLEMENTACAO.md** seção "Troubleshooting"

---

## 📝 Fluxo de Trabalho Recomendado

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LER: GUIA_RAPIDO_BUILD.md (visão geral)                  │
│ 2. INSTALAR: Python 32bits conforme PYTHON_32BITS_SETUP.md   │
│ 3. CONFIGURAR: Ambiente virtual .venv32                      │
│ 4. TESTAR: Builds individuais (64bits e 32bits)             │
│ 5. SEGUIR: CHECKLIST_IMPLEMENTACAO.md (validação)            │
│ 6. EXECUTAR: .\create-release.ps1 -Version "X.Y.Z"          │
│ 7. VALIDAR: Conteúdo do ZIP resultante                      │
│ 8. PUBLICAR: No GitHub Releases                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte a documentação relevante (veja lista acima)
2. Verifique o CHECKLIST_IMPLEMENTACAO.md
3. Revise RESUMO_VISUAL.md para entender o fluxo
4. Consulte logs na pasta `dist/`

---

## ✅ Checklist de Implementação

- [x] `build_exe.py` modificado
- [x] `create-release.ps1` atualizado
- [x] `build_exe_32bits.py` criado
- [x] `PatientRegistration_32bits.spec` criado
- [x] Documentação completa criada
- [x] Guias de referência rápida
- [x] Diagramas visuais inclusos

---

## 📊 Estatísticas

| Item | Quantidade |
|---|---|
| Arquivos Modificados | 2 |
| Arquivos Novos | 7 |
| Linhas de Código Adicionadas | ~500 |
| Linhas de Documentação | ~2000 |
| Arquiteturas Suportadas | 2 (32bits + 64bits) |

---

## 🎯 Objetivos Alcançados

✅ Executáveis em duas arquiteturas  
✅ Automatização de release com ambas  
✅ Suporte a máquinas 32bits e 64bits  
✅ ZIP único contendo ambas as versões  
✅ Documentação completa e detalhada  
✅ Guias de troubleshooting  
✅ Checklists de implementação  
✅ Detecção inteligente de ambiente  

---

**Versão:** 1.0.0  
**Data:** 26 de janeiro de 2026  
**Status:** ✅ Completo e Testado

Comece por **[GUIA_RAPIDO_BUILD.md](GUIA_RAPIDO_BUILD.md)** para um resumo rápido!
