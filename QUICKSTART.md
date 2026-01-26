# 🚀 QUICK START - Compilação 32 e 64 bits

## Em 3 Passos

### 1️⃣ Instale dependências (primeira vez)
```bash
pip install -r requirements.txt
```

### 2️⃣ Valide o sistema
```bash
python validate_system.py
```

### 3️⃣ Compile as versões
```bash
# Windows
build_releases.bat

# Linux/Mac
python build_releases.py
```

## Pronto! ✅

Os arquivos compilados estarão em:
- **64 bits**: `dist/64bits/prontuario-64bits/prontuario-sistema-64bits.exe`
- **32 bits**: `dist/32bits/prontuario-32bits/prontuario-sistema-32bits.exe`

---

## Problemas Comuns

| Erro | Solução |
|------|---------|
| `python: command not found` | Instale Python 3.7+ |
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Compilação demora | Normal (5-10 min) |
| Porta 5000 em uso | Feche outro programa ou edite `wsgi.py` |

---

## Distribuir

```bash
# Windows: Clique direito > Enviar para > Pasta compactada
# Crie: prontuario-v1.0.0-64bits.zip
#       prontuario-v1.0.0-32bits.zip
```

---

## Documentação Completa

- [RELEASES.md](RELEASES.md) - Overview
- [GUIA_COMPILACAO.md](GUIA_COMPILACAO.md) - Guia técnico
- [CHECKLIST_RELEASE.md](CHECKLIST_RELEASE.md) - Distribuição

---

**Dica**: Valide sempre com `python validate_system.py` antes de compilar!
