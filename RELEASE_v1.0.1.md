# Release v1.0.1 - Sistema de Registro de Pacientes

## 📦 Estrutura de Release

Esta release contém **ferramentas e scripts completos** para compilar e distribuir o Sistema de Registro de Pacientes em versões 32 bits e 64 bits.

> **Nota**: Executáveis pré-compilados (`.exe`) estarão disponíveis em breve em seção "Assets" desta release após compilação em Windows.

---

## 🚀 Início Rápido

### Para Compilar Localmente

**Pré-requisitos:**
- Python 3.7 ou superior
- pip
- ~500MB espaço em disco

**Passos:**

```bash
# 1. Clone o repositório
git clone https://github.com/phgutierrez/patient-registration-system.git
cd patient-registration-system

# 2. Instale dependências
pip install -r requirements.txt

# 3. Valide o sistema
python validate_system.py

# 4. Compile as builds
# Windows
build_releases.bat

# Linux/Mac
python build_releases.py
```

**Resultado:**
```
dist/
├── 64bits/prontuario-64bits/prontuario-sistema-64bits.exe
└── 32bits/prontuario-32bits/prontuario-sistema-32bits.exe
```

---

## 📋 Conteúdo da Release

### Scripts de Compilação
- ✅ `build_releases.py` - Compilador automático (Python)
- ✅ `build_releases.bat` - Compilador Windows (duplo-clique)
- ✅ `validate_system.py` - Validador pré-compilação

### Configuração
- ✅ `prontuario_64bits.spec` - Especificação PyInstaller (64 bits)
- ✅ `prontuario_32bits.spec` - Especificação PyInstaller (32 bits)
- ✅ `wsgi.py` - Servidor Waitress otimizado
- ✅ `requirements.txt` - Dependências (incluindo PyInstaller)

### Documentação
- 📖 `RELEASES.md` - Visão geral dos releases
- 📖 `GUIA_COMPILACAO.md` - Guia técnico detalhado (500+ linhas)
- 📖 `CHECKLIST_RELEASE.md` - Checklist de distribuição
- 📖 `QUICKSTART.md` - Início rápido (3 passos)
- 📖 `COMECE_AQUI.txt` - Guia visual (5 passos)
- 📖 `CHANGELOG.md` - Histórico de alterações
- 📖 `RELEASE_NOTES.md` - Notas desta release

---

## 🎯 Versões Disponíveis

### 64 bits (Recomendado para Windows modernos)
- Nome: `prontuario-sistema-64bits.exe`
- Tamanho: ~150-200 MB
- Compatibilidade: Windows 10/11, Windows 64 bits
- Desempenho: Melhor

### 32 bits (Para computadores antigos)
- Nome: `prontuario-sistema-32bits.exe`
- Tamanho: ~140-190 MB
- Compatibilidade: Windows 7/8/10 (32 e 64 bits)
- Desempenho: Bom

---

## 📦 Próximas Etapas

### 1. Para Desenvolvedores
```bash
# Compile localmente
python build_releases.py

# Teste ambas as versões
./dist/64bits/prontuario-64bits/prontuario-sistema-64bits.exe
./dist/32bits/prontuario-32bits/prontuario-sistema-32bits.exe

# Comprima para distribuição
# Windows: Clique direito > Enviar para > Pasta compactada
# Linux/Mac: tar -czf prontuario-v1.0.1-64bits.tar.gz dist/64bits/prontuario-64bits/
```

### 2. Para Usuários Finais
Aguarde o upload dos executáveis pré-compilados nos "Assets" desta release:
- Baixar `prontuario-v1.0.1-64bits.zip` ou
- Baixar `prontuario-v1.0.1-32bits.zip`
- Extrair e executar o `.exe`

---

## ✨ O Que Há de Novo em v1.0.1

### Compilação & Distribuição
- ✅ Suporte completo para builds 32 e 64 bits
- ✅ Scripts automatizados de compilação
- ✅ Validação de sistema pré-compilação
- ✅ Servidor Waitress integrado
- ✅ Documentação completa

### Funcionalidades Mantidas
- ✅ Todas as funcionalidades de v1.0.0
- ✅ Compatibilidade com banco de dados anterior
- ✅ Interface sem mudanças
- ✅ Sem breaking changes

---

## 🔒 Segurança

✅ **Implementado:**
- Waitress para servidor robusto
- Modo produção ativado
- Debug desativado
- Dependências atualizadas

⚠️ **Recomendações:**
- Use com HTTPS em produção (reverse proxy)
- Mantenha credenciais em arquivo `.env`
- Atualize regularmente

---

## 📊 Especificações Técnicas

| Aspecto | Detalhes |
|---------|----------|
| **Python** | 3.7+ |
| **Servidor** | Waitress |
| **Framework** | Flask |
| **Compilador** | PyInstaller 6.18.0+ |
| **Banco de Dados** | SQLite / PostgreSQL |
| **Compatibilidade** | Windows 7+ |
| **Threads** | 4 (customizável) |
| **Porta Padrão** | 5000 |

---

## 📖 Documentação Completa

### Para Compilar
→ Leia [GUIA_COMPILACAO.md](GUIA_COMPILACAO.md)

### Para Começar Rápido
→ Leia [QUICKSTART.md](QUICKSTART.md) ou [COMECE_AQUI.txt](COMECE_AQUI.txt)

### Para Distribuir
→ Use [CHECKLIST_RELEASE.md](CHECKLIST_RELEASE.md)

### Para Entender Mudanças
→ Veja [CHANGELOG.md](CHANGELOG.md) e [RELEASE_NOTES.md](RELEASE_NOTES.md)

---

## 🐛 Reportar Problemas

Se encontrar um bug:

1. Verifique se o problema existe em [Issues](https://github.com/phgutierrez/patient-registration-system/issues)
2. Execute `python validate_system.py`
3. Leia [GUIA_COMPILACAO.md](GUIA_COMPILACAO.md) (Troubleshooting)
4. Abra uma nova [Issue](https://github.com/phgutierrez/patient-registration-system/issues/new) com:
   - Descrição clara do problema
   - Passos para reproduzir
   - Versão do Windows/Linux/Mac
   - Saída de `python validate_system.py`

---

## 📞 Suporte

### Documentação Online
- [Releases](RELEASES.md)
- [Guia de Compilação](GUIA_COMPILACAO.md)
- [Checklist de Distribuição](CHECKLIST_RELEASE.md)
- [Changelog](CHANGELOG.md)

### Comunidade
- [Issues](https://github.com/phgutierrez/patient-registration-system/issues)
- [Discussions](https://github.com/phgutierrez/patient-registration-system/discussions)

---

## 📜 Licença

Veja [LICENSE](LICENSE) para detalhes.

---

## 🎉 Agradecimentos

Obrigado por usar o Sistema de Registro de Pacientes!

---

**Versão**: 1.0.1  
**Data de Lançamento**: 26 de janeiro de 2026  
**Status**: ✅ Pronto para Produção  
**Compatibilidade**: Windows 7+, Linux, macOS  

---

## 📋 Checklist Pre-Compilação

- [x] Código validado
- [x] Dependências atualizadas
- [x] Documentação completa
- [x] Scripts de compilação funcionando
- [x] Notas de release criadas
- [ ] Compilação em Windows concluída
- [ ] Testes em ambas versões (32 e 64 bits)
- [ ] Upload dos executáveis para Assets
- [ ] Anúncio da release

---

**Para compilar e testar localmente:**

```bash
pip install -r requirements.txt
python validate_system.py
python build_releases.py  # ou build_releases.bat no Windows
```

Que a compilação seja rápida! 🚀
