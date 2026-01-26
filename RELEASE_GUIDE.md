# 📦 Guia de Release - Como Publicar o Executável no GitHub

Este guia explica como adicionar o executável do sistema ao GitHub de forma **profissional** usando **GitHub Releases**.

---

## 🎯 Por que usar GitHub Releases?

### ❌ **NÃO** faça isso:
- Commitar o executável diretamente no repositório
- Adicionar binários grandes ao controle de versão
- Usar o git para rastrear mudanças em arquivos compilados

### ✅ **FAÇA** isso:
- Use **GitHub Releases** para distribuir binários
- Mantenha o repositório leve (apenas código-fonte)
- Organize versões com tags semânticas

### Vantagens do GitHub Releases:
- 📊 Histórico organizado de versões
- 📥 Downloads centralizados e rastreáveis
- 🏷️ Tags para cada versão (v1.0.0, v1.1.0, etc.)
- 📝 Changelog automático
- 🔗 Links permanentes para downloads
- 💾 Sem impacto no tamanho do repositório

---

## 🚀 Passo a Passo: Criar uma Release

### 1️⃣ Preparar o Executável

```powershell
# 1. Limpar arquivos anteriores
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# 2. Limpar arquivos .pyc
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 3. Criar novo build
python build_exe.py

# 4. Verificar se foi criado corretamente
Test-Path "dist\PatientRegistration\PatientRegistration.exe"
```

### 2️⃣ Comprimir a Pasta

```powershell
# Criar arquivo ZIP com toda a pasta
Compress-Archive -Path "dist\PatientRegistration" -DestinationPath "PatientRegistration-v1.0.0-windows.zip" -Force

# Verificar tamanho do arquivo
$size = (Get-Item "PatientRegistration-v1.0.0-windows.zip").Length / 1MB
Write-Host "Tamanho do arquivo: $([math]::Round($size, 2)) MB"
```

### 3️⃣ Criar Tag de Versão

```bash
# Commit todas as mudanças primeiro
git add .
git commit -m "Release v1.0.0 - Interface modernizada e otimizações"

# Criar e enviar a tag
git tag -a v1.0.0 -m "Versão 1.0.0 - Release Inicial"
git push origin v1.0.0
```

### 4️⃣ Criar Release no GitHub (via Interface Web)

1. **Acesse seu repositório** no GitHub
   ```
   https://github.com/phgutierrez/patient-registration-system
   ```

2. **Clique em "Releases"** no menu lateral direito

3. **Clique em "Create a new release"**

4. **Preencha os campos**:

   **Tag version**: `v1.0.0` (selecione a tag que você criou)

   **Release title**: `v1.0.0 - Sistema de Solicitação de Cirurgia`

   **Description**:
   ```markdown
   ## 🏥 Sistema de Solicitação de Cirurgia - Ortopedia Pediátrica
   
   ### ✨ Novidades desta versão
   
   - 🎨 Interface moderna com gradientes e animações
   - ⚡ Modo --onedir para inicialização ultra-rápida
   - 🖼️ Logo institucional na sidebar
   - 🎯 Cards clicáveis em toda área
   - 📝 Todos os templates modernizados
   - 🐛 Correções de bugs visuais
   
   ### 📥 Instalação
   
   1. **Baixe** o arquivo `PatientRegistration-v1.0.0-windows.zip`
   2. **Extraia** todo o conteúdo para uma pasta
   3. **Execute** `PatientRegistration.exe` dentro da pasta extraída
   4. O sistema abrirá automaticamente no navegador
   
   ### 📊 Informações Técnicas
   
   - **Tamanho**: ~170 MB (comprimido) / 377 MB (extraído)
   - **Plataforma**: Windows 10/11
   - **Python**: 3.11.9
   - **Servidor**: Waitress 2.1.2
   
   ### 🔧 Requisitos
   
   - Windows 10 ou superior
   - Navegador web moderno (Chrome, Edge, Firefox)
   - **Não requer instalação de Python**
   
   ### 📝 Primeira Execução
   
   O sistema criará automaticamente:
   - Banco de dados SQLite
   - 5 usuários iniciais (pedro, andre, brauner, savio, laecio)
   - Estrutura de pastas necessária
   
   ### ⚠️ Importante
   
   - Envie **toda a pasta extraída**, não apenas o .exe
   - O banco de dados fica em `instance/prontuario.db`
   - Para backup, copie a pasta `instance`
   
   ### 🐛 Problemas Conhecidos
   
   Nenhum neste momento. Reporte bugs em [Issues](https://github.com/phgutierrez/patient-registration-system/issues)
   
   ---
   
   **Desenvolvido por Dr. Pedro Henrique Freitas © 2026**
   ```

5. **Anexar o arquivo ZIP**:
   - Arraste e solte `PatientRegistration-v1.0.0-windows.zip` na área "Attach binaries"
   - Ou clique em "Attach binaries by dropping them here or selecting them"

6. **Marcar como "Latest release"** ✅

7. **Clicar em "Publish release"** 🚀

---

## 🔄 Releases Futuras

### Versionamento Semântico (Semantic Versioning)

Use o formato `MAJOR.MINOR.PATCH` (ex: v1.2.3):

- **MAJOR** (v2.0.0): Mudanças incompatíveis com versões anteriores
- **MINOR** (v1.1.0): Novas funcionalidades compatíveis
- **PATCH** (v1.0.1): Correções de bugs

### Exemplo de Release v1.1.0

```bash
# 1. Fazer mudanças e commits
git add .
git commit -m "Adiciona funcionalidade X"

# 2. Criar build atualizado
python build_exe.py

# 3. Comprimir
Compress-Archive -Path "dist\PatientRegistration" -DestinationPath "PatientRegistration-v1.1.0-windows.zip" -Force

# 4. Tag e push
git tag -a v1.1.0 -m "Versão 1.1.0 - Nova funcionalidade X"
git push origin v1.1.0

# 5. Criar release no GitHub e anexar o ZIP
```

---

## 🛠️ Alternativa: GitHub CLI (gh)

### Criar release via linha de comando

```bash
# Instalar GitHub CLI
# Download: https://cli.github.com/

# Login
gh auth login

# Criar release com arquivo
gh release create v1.0.0 \
  PatientRegistration-v1.0.0-windows.zip \
  --title "v1.0.0 - Sistema de Solicitação de Cirurgia" \
  --notes "Release inicial com interface moderna e otimizações"
```

---

## 📊 Exemplo de Estrutura de Releases

```
v1.0.0 (Latest) - Janeiro 2026
├── PatientRegistration-v1.0.0-windows.zip (170 MB)
└── Source code (zip)
└── Source code (tar.gz)

v1.0.1 - Correções de bugs
v1.1.0 - Nova funcionalidade: Relatórios
v2.0.0 - Mudanças significativas
```

---

## ✅ Checklist de Release

Antes de publicar uma release, verifique:

- [ ] Build executado com sucesso
- [ ] Executável testado em máquina limpa
- [ ] Banco de dados está sendo criado corretamente
- [ ] Todos os templates carregam sem erros
- [ ] Versão atualizada no código (se aplicável)
- [ ] Changelog documentado
- [ ] Tag criada com nome correto (v1.0.0)
- [ ] ZIP criado com nome descritivo
- [ ] README atualizado
- [ ] Release notes escritas

---

## 📝 Notas Adicionais

### .gitignore Recomendado

Adicione ao `.gitignore`:

```gitignore
# Builds e distribuição
build/
dist/
*.exe
*.zip
*.spec

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/

# Virtual environment
.venv/
venv/
ENV/

# Banco de dados
instance/
*.db
*.sqlite

# IDEs
.vscode/
.idea/
*.swp
```

### Tamanho dos Arquivos

GitHub permite arquivos até **2 GB** por release. O executável atual (~170 MB comprimido) está bem dentro do limite.

### Múltiplas Plataformas

Para distribuir em múltiplas plataformas:

```
PatientRegistration-v1.0.0-windows.zip
PatientRegistration-v1.0.0-linux.tar.gz
PatientRegistration-v1.0.0-macos.dmg
```

---

## 🎯 Resultado Final

Após seguir este guia, seus usuários poderão:

1. Acessar https://github.com/phgutierrez/patient-registration-system/releases
2. Ver a última versão destacada
3. Ler o changelog completo
4. Baixar o executável com um clique
5. Acessar versões anteriores se necessário

---

## 📚 Recursos Adicionais

- [Documentação GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/lang/pt-BR/)
- [GitHub CLI](https://cli.github.com/)

---

<div align="center">

**Boas práticas para distribuição profissional de software!** 🚀

</div>
