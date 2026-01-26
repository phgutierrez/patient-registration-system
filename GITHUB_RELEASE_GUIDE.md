# 📋 Instruções para GitHub Release v1.0.1

## Passo a Passo para Publicar no GitHub

### 1️⃣ Preparar o Git

```bash
# Navegar até o projeto
cd /Users/pedrofreitas/Programacao/patient-registration-system

# Verificar status
git status

# Adicionar todos os arquivos novos
git add .

# Verificar o que será commitado
git status

# Fazer commit com mensagem clara
git commit -m "Release v1.0.1: Suporte para compilação 32 e 64 bits com PyInstaller"
```

### 2️⃣ Fazer Tag da Release

```bash
# Criar tag anotada
git tag -a v1.0.1 -m "Versão 1.0.1 - Sistema de Registro de Pacientes com suporte 32 e 64 bits"

# Verificar tag
git tag -l -n1

# Enviar para remoto
git push origin master
git push origin v1.0.1
```

### 3️⃣ Criar Release no GitHub

No GitHub, vá para:
**Releases** → **Draft a new release**

**Ou use a CLI (GitHub CLI):**

```bash
# Se não tiver gh CLI, instale:
# brew install gh

# Fazer login
gh auth login

# Criar release
gh release create v1.0.1 \
  --title "Sistema de Registro de Pacientes v1.0.1" \
  --notes-file RELEASE_v1.0.1.md \
  --draft
```

### 4️⃣ Preencher Informações no GitHub

**Nome da Release:**
```
Sistema de Registro de Pacientes v1.0.1
```

**Descrição (Body):**

Copie o conteúdo de [RELEASE_v1.0.1.md](RELEASE_v1.0.1.md)

**Ou use CLI:**
```bash
gh release edit v1.0.1 --notes-file RELEASE_v1.0.1.md
```

### 5️⃣ Upload de Arquivos (Assets)

#### Opção A: Via GitHub Website

1. Vá para a release draft
2. Clique em "Attach binaries by dropping them here or selecting them."
3. Selecione os arquivos:
   - Quando compilar em Windows: `prontuario-v1.0.1-64bits.zip`
   - Quando compilar em Windows: `prontuario-v1.0.1-32bits.zip`
   - Opcional: `CHANGELOG.md`
   - Opcional: `RELEASE_NOTES.md`

#### Opção B: Via GitHub CLI

```bash
# Após compilar, comprimir os arquivos:
cd dist/64bits && zip -r ../../prontuario-v1.0.1-64bits.zip prontuario-64bits/
cd ../32bits && zip -r ../../prontuario-v1.0.1-32bits.zip prontuario-32bits/

# Depois fazer upload
gh release upload v1.0.1 prontuario-v1.0.1-64bits.zip
gh release upload v1.0.1 prontuario-v1.0.1-32bits.zip
```

### 6️⃣ Publicar Release

**Via Website:**
- Clique no botão **"Publish release"** (sair de draft)

**Via CLI:**
```bash
# Se ainda está em draft, publicar
gh release edit v1.0.1 --draft=false
```

---

## 📋 Checklist Final

### Antes de Publicar

- [ ] Código commitado: `git log --oneline -5`
- [ ] Tag criada: `git tag -l -n1`
- [ ] Push feito: `git push origin master && git push origin v1.0.1`

### Executáveis (quando compilado em Windows)

- [ ] `prontuario-v1.0.1-64bits.zip` criado (~50-70 MB)
- [ ] `prontuario-v1.0.1-32bits.zip` criado (~50-70 MB)
- [ ] Ambos os arquivos testados após extração
- [ ] Ambos uploadados no GitHub Release

### Documentação

- [ ] RELEASE_v1.0.1.md preenchido na release
- [ ] CHANGELOG.md listado em Assets
- [ ] RELEASE_NOTES.md listado em Assets

### Anúncio

- [ ] Release publicada (não mais draft)
- [ ] Tweetar/compartilhar (opcional)
- [ ] Adicionar link na documentação

---

## 🔍 Verificação Pós-Release

```bash
# Verificar tag
git describe --tags

# Listar releases
gh release list

# Ver detalhes da release
gh release view v1.0.1

# Fazer download dos assets (testar)
gh release download v1.0.1
```

---

## 📝 Exemplo de Release Notes

Quando ir ao GitHub Release e preencher:

```markdown
## 📦 Sistema de Registro de Pacientes v1.0.1

**Data**: 26 de janeiro de 2026

### ✨ Principais Mudanças

- Suporte para compilação 32 bits e 64 bits
- Servidor Waitress integrado
- Scripts de compilação automatizados
- Documentação completa

### 📥 Download

- **64 bits**: `prontuario-v1.0.1-64bits.zip` (recomendado)
- **32 bits**: `prontuario-v1.0.1-32bits.zip`

### 🚀 Como Usar

1. Extraia o arquivo .zip
2. Duplo-clique no .exe
3. Sistema inicia automaticamente

### 📖 Documentação

Veja [RELEASE_NOTES.md](RELEASE_NOTES.md) para detalhes completos.

[Ver todos os detalhes](https://github.com/phgutierrez/patient-registration-system/releases/tag/v1.0.1)
```

---

## 🛠️ Correções (Se Necessário)

### Se cometeu um erro no commit

```bash
# Desfazer último commit (mantendo mudanças)
git reset HEAD~1

# Ou emendar último commit
git commit --amend -m "Nova mensagem"
```

### Se a tag está errada

```bash
# Deletar tag local
git tag -d v1.0.1

# Deletar tag remota
git push origin --delete v1.0.1

# Recriar
git tag -a v1.0.1 -m "Nova mensagem"
git push origin v1.0.1
```

### Se publicou release errada

```bash
# Deletar release (mas manter tag)
gh release delete v1.0.1

# Recriar
gh release create v1.0.1 --notes-file RELEASE_v1.0.1.md
```

---

## 📚 Referências

- [GitHub Releases Docs](https://docs.github.com/releases)
- [GitHub CLI](https://cli.github.com)
- [Semantic Versioning](https://semver.org/lang/pt_BR/)

---

## ⏰ Próximos Passos

1. ✅ Commit e push do código
2. ✅ Criar tag v1.0.1
3. ⏳ Compilar em Windows (quando possível)
4. ⏳ Comprimir executáveis
5. ⏳ Upload para GitHub Release
6. ⏳ Publicar release
7. ⏳ Anunciar aos usuários

---

**Status**: Pronto para Publicação  
**Requer**: Compilação em Windows (para executáveis)  
**Data**: 26 de janeiro de 2026
