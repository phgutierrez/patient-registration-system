# Notas de versão — 2.7.0 (novembro de 2026)

## Para os usuários

- **PDF de internação**: quando a solicitação marca *Reserva de Vaga UTI*, a
  página "AVISO DE CIRURGIA" mostra uma faixa verde com **RESERVAR VAGA DE UTI**
  abaixo da data de internação.
- **Requisição de hemocomponente**: a data impressa é sempre a data de
  internação do paciente. A data de exemplo do formulário (03/05/2024) não
  aparece mais.
- **Pacientes**: a busca atualiza a lista enquanto você digita, sem recarregar
  a página.
- **Agenda**: avançar/voltar período, trocar Semana/Mês e filtrar não recarregam
  mais a tela inteira.
- **Menu em telas pequenas**: o botão ☰ voltou a aparecer.

## Para quem instala/atualiza

- Sem mudança no banco de dados e sem novo pareamento das estações.
- Passo a passo por tipo de instalação (rede, EXE local, Python):
  [docs/ATUALIZACAO_V2.7.md](docs/ATUALIZACAO_V2.7.md).
- Segurança: Werkzeug atualizado para 3.1.9.
- Mudanças técnicas: [docs/CHANGELOG_V2.7.md](docs/CHANGELOG_V2.7.md).
