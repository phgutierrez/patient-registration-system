# Notas de versão — 2.8.0 (novembro de 2026)

## Para os usuários

- **Excluir solicitação de cirurgia.** Há um botão de lixeira na lista de
  solicitações do paciente, na tela da solicitação e na lista de pendências.
  - Pode excluir quem criou a solicitação ou um administrador.
  - Solicitações antigas, sem autor registrado, só podem ser excluídas por um administrador.
  - O sistema sempre pede confirmação antes de excluir.
  - Se a solicitação já foi enviada à agenda, um aviso lembra de **apagar o
    evento manualmente no Google Agenda**. O sistema não remove eventos do Google.
- **Pendências clicáveis.** O card *Solicitações pendentes* do início abre a
  nova tela **Pendências**, que também está no menu lateral.
  - A tela mostra as suas pendências e tem a opção *Todas da especialidade*.
  - Datas já passadas ficam destacadas em vermelho.
- **Minhas próximas cirurgias.** O início mostra só as cirurgias que você
  solicitou ou em que você é o assistente. A **Agenda Cirúrgica** continua
  mostrando todos os agendamentos.
- **Formulário de solicitação mais prático.** Todos os campos e funções
  continuam iguais. As novidades são:
  - campos obrigatórios marcados com `*`;
  - o menu de seções mostra quantos obrigatórios faltam em cada parte (ou ✓);
  - ao clicar em *Gerar solicitação*, a lista do que falta aparece antes de
    enviar, com link para cada campo;
  - **rascunho automático** neste computador: se a página fechar, ao voltar
    aparece *Restaurar rascunho*;
  - atalhos de duração (1 h–4 h), de data (amanhã, +7, +15 dias) e de
    horário (07:00, 13:00);
  - na busca de procedimento, *Enter* escolhe quando sobra uma única opção e
    *Esc* limpa a busca;
  - o botão não envia duas vezes.
- **Edição de paciente.** Agora tem as mesmas máscaras do cadastro novo (CNS,
  telefone, CID, UF), não envia duas vezes e não repete mais as mensagens.

## Correções

- **Build do executável.** Em computadores sem Node.js, o build parava
  procurando `app-shell.js` em `js/pages`. O caminho foi corrigido.
- **Agenda.** Marcar um evento como Realizada ou Suspensa voltou a atualizar a
  solicitação ligada a ele. O identificador gravado no evento não era reconhecido.
- **Mensagem de PDF indisponível.** Esse caso causava erro interno; agora
  volta para a tela da solicitação.

## Para quem instala ou atualiza

- Não há mudança no banco de dados, não é preciso parear as estações de novo e
  as dependências Python (`requirements.txt`) são as mesmas.
- Passo a passo para cada tipo de instalação:
  [docs/ATUALIZACAO_V2.8.md](docs/ATUALIZACAO_V2.8.md).
