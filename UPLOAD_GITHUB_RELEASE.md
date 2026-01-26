# 📦 GitHub Release v1.0.1 - Instruções de Upload

## ✅ Arquivos Prontos

Os seguintes arquivos foram preparados para upload:

```
dist/
├── prontuario-v1.0.1-64bits.zip  (627 KB - compatível com Windows 64 bits)
├── prontuario-v1.0.1-32bits.zip  (627 KB - compatível com Windows 32 bits)
└── 64bits/
    └── prontuario-64bits/        (estrutura com templates, static, database)
└── 32bits/
    └── prontuario-32bits/        (estrutura com templates, static, database)
```

## 🚀 Como Fazer Upload para GitHub Release

### Opção 1: Via Website GitHub (Recomendado - Simples)

#### Passo 1: Acessar página de Releases

1. Acesse seu repositório no GitHub:
   ```
   https://github.com/phgutierrez/patient-registration-system
   ```

2. Clique em "Releases" (lado direito)
   ```
   Você verá: Releases (ao lado de "Packages" e "Deployments")
   ```

#### Passo 2: Criar novo Release

1. Clique em "Create a new release" ou "Draft a new release"

2. Na tela de criação:

   **Tag version:**
   ```
   v1.0.1
   ```
   (Selecione a tag já existente se aparecer um dropdown)

   **Release title:**
   ```
   Sistema de Registro de Pacientes v1.0.1
   ```

   **Describe this release:**
   ```
   Copie o conteúdo de RELEASE_v1.0.1.md e cole aqui
   
   Ou resumidamente:
   
   ## 📋 Principais Mudanças
   
   - ✅ Compilação 32 e 64 bits com PyInstaller
   - ✅ Compatibilidade Windows 7+
   - ✅ Servidor WSGI otimizado (Waitress)
   - ✅ Documentação completa
   - ✅ Scripts de compilação automática
   
   ## 📥 Como Instalar
   
   1. Baixe o arquivo correspondente à sua versão:
      - **64 bits**: `prontuario-v1.0.1-64bits.zip`
      - **32 bits**: `prontuario-v1.0.1-32bits.zip`
   
   2. Extraia o arquivo
   
   3. Execute: `prontuario-64bits.exe` ou `prontuario-32bits.exe`
   
   ## 🔧 Requisitos
   
   - Windows 7 ou superior
   - Mínimo 512 MB de RAM
   - 300 MB de espaço em disco
   
   ## 📚 Documentação
   
   Consulte os arquivos no repositório:
   - GUIA_COMPILACAO.md - Guia técnico de compilação
   - README.md - Documentação geral
   ```

#### Passo 3: Fazer Upload dos Arquivos

1. Na seção **"Attach binaries by dropping them here or selecting them"**

2. Clique e selecione os dois arquivos:
   ```
   prontuario-v1.0.1-64bits.zip
   prontuario-v1.0.1-32bits.zip
   ```

   Ou arraste os arquivos diretamente

3. Aguarde o upload (barra de progresso aparecerá)

#### Passo 4: Publicar Release

1. Se tudo está correto, clique em "Publish release"

2. Verifique se:
   - ✅ Release aparece em https://github.com/phgutierrez/patient-registration-system/releases
   - ✅ Tag v1.0.1 está selecionada
   - ✅ Arquivos ZIP estão listados em "Assets"
   - ✅ Descrição está formatada corretamente

---

### Opção 2: Via GitHub CLI (Automático)

Se você tem GitHub CLI instalado (`gh`):

#### Passo 1: Fazer login

```bash
gh auth login
```

#### Passo 2: Criar Release com Descrição

```bash
cd /Users/pedrofreitas/Programacao/patient-registration-system

gh release create v1.0.1 \
  --title "Sistema de Registro de Pacientes v1.0.1" \
  --notes-file RELEASE_v1.0.1.md \
  dist/prontuario-v1.0.1-64bits.zip \
  dist/prontuario-v1.0.1-32bits.zip
```

#### Passo 3: Verificar

```bash
gh release view v1.0.1
```

---

### Opção 3: Via Curl (Avançado)

Se preferir linha de comando:

```bash
# 1. Obter token do GitHub
# Settings → Developer settings → Personal access tokens → Generate new token
# Escopo: repo (full control of private repositories)

export GITHUB_TOKEN="seu_token_aqui"
export OWNER="phgutierrez"
export REPO="patient-registration-system"
export TAG="v1.0.1"

# 2. Upload 64 bits
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/zip" \
  --data-binary @dist/prontuario-v1.0.1-64bits.zip \
  "https://uploads.github.com/repos/$OWNER/$REPO/releases/by-tag/$TAG/assets?name=prontuario-v1.0.1-64bits.zip"

# 3. Upload 32 bits
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/zip" \
  --data-binary @dist/prontuario-v1.0.1-32bits.zip \
  "https://uploads.github.com/repos/$OWNER/$REPO/releases/by-tag/$TAG/assets?name=prontuario-v1.0.1-32bits.zip"
```

---

## ✨ Após o Upload - Checklist Final

- [ ] Release visível em "Releases"
- [ ] Tag v1.0.1 aparece em "Tags"
- [ ] Descrição está formatada corretamente
- [ ] 2 arquivos ZIP listados em "Assets"
- [ ] Tamanho dos arquivos está correto (~627 KB cada)
- [ ] Release pode ser baixado pelos usuários
- [ ] Links funcionam
- [ ] README.md aponta para a release

---

## 📖 Conteúdo Recomendado para Descrição

Copie e adapte de `RELEASE_v1.0.1.md`:

```markdown
# v1.0.1 - Sistema de Registro de Pacientes

## 🎯 Destaques

- Compilação profissional com PyInstaller
- Suporte para Windows 32 e 64 bits
- Servidor WSGI otimizado (Waitress)
- Interface web responsiva
- Banco de dados integrado
- Documentação completa

## 📥 Download

Escolha a versão compatível com seu Windows:

- **Windows 64 bits** (máquinas modernas): `prontuario-v1.0.1-64bits.zip`
- **Windows 32 bits** (máquinas antigas): `prontuario-v1.0.1-32bits.zip`

## 🚀 Como Usar

1. Extraia o arquivo ZIP
2. Execute o arquivo `.exe`
3. O aplicativo abrirá em `http://localhost:5000`
4. Faça login com suas credenciais

## 💻 Requisitos Mínimos

- Windows 7 ou superior
- 512 MB RAM
- 300 MB espaço livre

## 📝 Notas da Versão

Veja [CHANGELOG.md](CHANGELOG.md) para lista completa de mudanças

## 🔗 Links Úteis

- Repositório: https://github.com/phgutierrez/patient-registration-system
- Documentação: [README.md](README.md)
- Guia de Compilação: [GUIA_COMPILACAO.md](GUIA_COMPILACAO.md)

---

Desenvolvido em 26 de janeiro de 2026
```

---

## 🎯 Dicas Importantes

✅ **Para o Título**: Use apenas o versão + descrição breve  
✅ **Para a Descrição**: Use Markdown formatado  
✅ **Arquivos**: Certifique-se que são .zip (não rar, 7z, tar.gz)  
✅ **Tamanho**: Normal ter ~600 KB (inclui Python runtime)  
✅ **Release Draft**: Se não tiver certeza, deixe como rascunho antes de publicar  

❌ **Evite**: Subir arquivos .exe diretamente (use ZIP)  
❌ **Evite**: Descrições sem formatação (use Markdown)  
❌ **Evite**: Publicar sem testar os downloads  

---

## 🆘 Troubleshooting

### Erro: "Tag v1.0.1 não existe"
→ A tag foi criada. Se não aparecer, try `git push --tags`

### Erro: "Assets não aparecem"
→ Aguarde alguns segundos após o upload  
→ Recarregue a página (F5)  

### Arquivo ZIP está corrompido
→ Verifique: `unzip -t prontuario-v1.0.1-64bits.zip`  
→ Se falhar, recrie: `zip -r prontuario-v1.0.1-64bits.zip dist/64bits/prontuario-64bits/`  

### Release não aparece para usuários
→ Certifique-se que clicou "Publish release" (não "Save as draft")  
→ Release privada? → Mudar para "Public" nas configurações do repositório  

---

## ✅ Status Atual

| Componente | Status | Detalhes |
|-----------|--------|----------|
| Tag v1.0.1 | ✅ Criada | Existente no GitHub |
| Arquivos ZIP | ✅ Prontos | 627 KB cada |
| Documentação | ✅ Completa | 5000+ linhas |
| Git Push | ✅ Sincronizado | master + tags enviadas |
| Release GitHub | ⏳ Aguardando | Manualmente via website |

---

**Próximo passo**: Realizar upload dos ZIPs para a release no GitHub! 🚀

Data: 26 de janeiro de 2026  
Versão: 1.0.1
