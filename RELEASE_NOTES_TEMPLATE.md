## 🏥 Sistema de Solicitação de Cirurgia - Ortopedia Pediátrica

### ✨ Novidades desta versão

- � **Suporte Multi-Arquitetura**: Agora disponível em versões 32 e 64 bits
- ⚡ Executáveis otimizados para Windows 10/11 (32 e 64 bits)
- 📦 Pacote unificado com ambas as versões
- �🎨 Interface moderna com gradientes e animações suaves
- ⚡ Modo --onedir para inicialização ultra-rápida
- 🖼️ Logo institucional posicionado na sidebar inferior esquerda
- 🎯 Cards do dashboard totalmente clicáveis
- 📝 Todos os 17 templates modernizados com novo padrão visual
- 🎨 Headers com gradientes escuro (135deg, #1e293b → #0f172a)
- 🔘 Botões com efeitos hover e elevação
- 📱 Design responsivo aprimorado
- 🐛 Correção de logo duplicado que quebrava layouts
- 🧹 Otimizações de performance e limpeza de código

### 📥 Instalação

#### Windows 10/11

1. **Baixe** o arquivo `PatientRegistration-v1.0.1-windows.zip` abaixo
2. **Extraia** todo o conteúdo para uma pasta de sua escolha
3. **Execute** o arquivo apropriado:
   - **Windows 64 bits** (recomendado): `PatientRegistration-64bit.exe`
   - **Windows 32 bits**: `PatientRegistration-32bit.exe`
4. O sistema abrirá automaticamente no navegador padrão

> ⚠️ **IMPORTANTE**: Mantenha todos os arquivos juntos na mesma pasta!

### 📊 Informações Técnicas

| Item | Detalhes |
|------|----------|
| **Tamanho Comprimido** | ~180 MB |
| **Tamanho Extraído** | ~400 MB |
| **Plataforma** | Windows 10/11 (32 e 64 bits) |
| **Python Interno** | 3.11.9 |
| **Servidor Web** | Waitress 2.1.2 |
| **Banco de Dados** | SQLite 3 |
| **Framework** | Flask 2.3.3 |

### 🔧 Requisitos do Sistema

- ✅ Windows 10 ou superior (32 ou 64 bits)
- ✅ Navegador web moderno (Chrome, Edge, Firefox)
- ✅ 500 MB de espaço em disco
- ✅ **Não requer instalação de Python ou dependências**
- ℹ️ Use a versão 64 bits se seu sistema suportar (recomendado)

### 📝 Primeira Execução

Na primeira vez que você executar o sistema:

1. **Banco de dados** será criado automaticamente em `instance/prontuario.db`
2. **5 usuários iniciais** serão criados:
   - pedro
   - andre
   - brauner
   - savio
   - laecio
3. **Estrutura de pastas** será gerada automaticamente

### 🎯 Funcionalidades Principais

#### Gestão de Pacientes
- ✅ Cadastro completo (dados pessoais, endereço, informações médicas)
- ✅ Busca e listagem com filtros
- ✅ Edição e visualização de prontuários
- ✅ Validação automática (CNS, CID, telefone)
- ✅ Cálculo automático de idade

#### Solicitações de Cirurgia
- ✅ Formulário detalhado para solicitação
- ✅ Geração automática de PDF
- ✅ Download de documentos
- ✅ Histórico completo

#### Interface
- ✅ Dashboard com atalhos (Alt+N, Alt+L, Alt+U)
- ✅ Cards clicáveis para navegação rápida
- ✅ Design moderno com gradientes
- ✅ Feedback visual em tempo real

### 💡 Dicas de Uso

- **Backup**: Copie a pasta `instance` regularmente para backup dos dados
- **Portabilidade**: Toda a pasta pode ser movida para outro local sem problemas
- **Múltiplos usuários**: Cada usuário pode ter seu próprio sistema em pastas diferentes
- **Atalhos de teclado**:
  - `Alt + N` - Cadastrar novo paciente
  - `Alt + L` - Listar pacientes
  - `Alt + U` - Cadastrar usuário

### 🐛 Problemas Conhecidos

Nenhum problema conhecido nesta versão. 

Para reportar bugs, abra uma [Issue](https://github.com/phgutierrez/patient-registration-system/issues/new).

### 🔄 Atualizações Futuras Planejadas

- [ ] Relatórios em PDF
- [ ] Exportação para Excel
- [ ] Gráficos estatísticos
- [ ] Sistema de backup automático
- [ ] Integração com prontuário eletrônico

### 📚 Documentação

- [README.md](https://github.com/phgutierrez/patient-registration-system#readme) - Documentação completa
- [RELEASE_GUIDE.md](https://github.com/phgutierrez/patient-registration-system/blob/master/RELEASE_GUIDE.md) - Guia para desenvolvedores

### 🆘 Suporte

Encontrou algum problema? Precisa de ajuda?

1. Consulte a [documentação](https://github.com/phgutierrez/patient-registration-system#readme)
2. Verifique as [Issues existentes](https://github.com/phgutierrez/patient-registration-system/issues)
3. Abra uma [nova Issue](https://github.com/phgutierrez/patient-registration-system/issues/new) se necessário

### 📄 Changelog Detalhado

#### v1.0.1 (26/01/2026)
- ✨ Adicionado suporte para Windows 32 bits
- 📦 Pacote agora inclui executáveis 32 e 64 bits
- 📝 README.txt incluído no pacote com instruções
- 🔧 Script de build multi-arquitetura criado

#### v1.0.0 (26/01/2026)
**Interface:**
- Novo sistema de cores com gradientes profissionais
- Logo reposicionado na sidebar (inferior esquerdo)
- Cards do dashboard agora são clicáveis em toda área
- Formulários com inputs modernos e ícones integrados
- Tabelas com hover effects e transformações suaves

**Performance:**
- Modo --onedir para inicialização instantânea
- Otimização de assets e dependências
- Remoção de módulos não utilizados
- Cache melhorado

**Correções:**
- ✅ Logo duplicado que quebrava layouts
- ✅ Espaçamento inconsistente entre elementos
- ✅ Responsividade em telas menores

---

### 👨‍⚕️ Créditos

**Desenvolvido por Dr. Pedro Henrique Freitas**

Sistema desenvolvido para otimização de processos em Ortopedia Pediátrica

© 2026 - Todos os direitos reservados

---

### 📝 Notas Adicionais

- **Novidade v1.0.1**: Agora com suporte completo para Windows 32 e 64 bits
- Para verificar sua arquitetura: Painel de Controle → Sistema
- Testado extensivamente em ambiente de produção
- Todos os dados são armazenados localmente (privacidade garantida)
- Sistema 100% offline após instalação

---

<div align="center">

**Desenvolvido com ❤️ para Ortopedia Pediátrica**

Se este projeto foi útil, considere dar uma ⭐ no repositório!

</div>
