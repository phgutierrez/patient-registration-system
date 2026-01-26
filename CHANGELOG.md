# CHANGELOG

## [1.0.1] - 26 de janeiro de 2026

### Adicionado
- ✨ Suporte para compilação 32 bits e 64 bits
- ✨ Servidor Waitress integrado para produção
- ✨ Scripts de compilação automatizados (build_releases.py)
- ✨ Validação de sistema pré-compilação (validate_system.py)
- ✨ Documentação completa para compilação e distribuição
- ✨ Arquivos .spec para PyInstaller (prontuario_64bits.spec, prontuario_32bits.spec)
- ✨ Checklist de release para distribuição profissional

### Melhorado
- 🔧 Configuração wsgi.py otimizada para modo produção
- 🔧 requirements.txt com dependências de build
- 🔧 Estrutura de projeto melhorada para empacotamento

### Documentação
- 📚 RELEASES.md - Visão geral dos releases
- 📚 GUIA_COMPILACAO.md - Guia técnico completo
- 📚 CHECKLIST_RELEASE.md - Checklist de distribuição
- 📚 QUICKSTART.md - Início rápido em 3 passos
- 📚 COMECE_AQUI.txt - Guia visual de 5 passos

### Notas Técnicas
- Python 3.7+ compatível
- Waitress para servidor robusto em produção
- PyInstaller para empacotamento executável
- Suporta Windows 7+, Linux, macOS

### Próximas Versões
- [ ] Executáveis pré-compilados no GitHub
- [ ] Instalador Windows (.msi)
- [ ] Suporte para autoupdate
- [ ] Notarização macOS

---

## [1.0.0] - Data Original

Primeira versão do Sistema de Registro de Pacientes com:
- Cadastro e gerenciamento de pacientes
- Solicitação e agendamento de cirurgias
- Geração automática de PDFs
- Integração com banco de dados
- Interface responsiva com Bootstrap
