# Notas de versão — 3.0.0 (novembro de 2026)

## Para os usuários

- **Controle de cirurgias (somente administradores).** Nova tela no menu lateral
  (*Controle de Cirurgias*) com as cirurgias de **ortopedia** lidas do banco
  Access do CPAM. A tela é **somente leitura**: não edita status, não cancela
  cirurgias e não grava nada no Access.
  - **Calendário mensal e semanal**, baseado na **data programada**
    (`dt_prov_CIR`). A semana começa na **segunda-feira**. O período atual é o
    padrão, com botões *anterior*, *próximo* e *Hoje*.
  - **Clique em um dia** para ver as cirurgias dele.
  - **Indicadores do período:** canceladas, realizadas e sem resposta do bloco
    (a partir de `CIRURGIA_agendada`: 0 = cancelada, 1 = realizada,
    vazio = sem resposta do bloco). Qualquer outro valor aparece como
    **status desconhecido**, nunca é classificado errado nem descartado.
  - **Lista filtrável** por status e por paciente/prontuário, com prontuário,
    paciente, data de cadastro, médico solicitante, procedimento (nome e código
    SUS), data programada, observações e status.
  - **Motivos de cancelamento:** a suspensão registrada em `tb_susp_cir` é associada à cirurgia **cancelada** por paciente,
    especialidade e data da cirurgia (`tb_susp_cir`), sem diferenciar maiúsculas,
    acentos e espaços. Mostra o **grupo** (`MOTIVO`) e a **descrição**.
    - Sem correspondência: *Motivo não localizado*.
    - Mais de uma correspondência: *Vínculo ambíguo*. Nenhum motivo é
      apresentado como confirmado.
  - **Resumo dos motivos de cancelamento** no período, agrupado por `MOTIVO`, com
    contagem e as descrições dos casos.
  - **Cirurgias sem data programada** (ou com data inválida) são avisadas na
    tela e **não aparecem no calendário**; uma lista própria permite consultá-las.
  - Se o Access estiver indisponível, a tela explica o que verificar
    (configuração, driver ou estrutura do banco), sem expor caminhos ou dados.
- A data de cadastro (`dt_atend_cons`) é só informativa: não é a data da cirurgia.

## Requisitos

- Usuário **administrador**. Médicos comuns e usuários sem login recebem
  "acesso negado" ou são enviados ao login, inclusive por URL direta.
- O Access configurado em *Configurações* deve conter:
  - `Ocorrencias_SS` com `prontuario`, nome do paciente, `dt_atend_cons`,
    `nome_medico_cons`, `especialidade_cons`, `procedimento_cir`, `dt_prov_CIR`,
    `orientaçao_ss` e `CIRURGIA_agendada`;
  - `tb_procedimentos_BC` (nome do procedimento a partir do código SUS);
  - `tb_susp_cir` com paciente, especialidade, `DATA_CIR`, `MOTIVO` e `descricao`.
- Se `tb_procedimentos_BC` ou `tb_susp_cir` não puderem ser lidas, as cirurgias
  continuam visíveis e a tela avisa que nomes/motivos estão indisponíveis.

## Técnico

- Sem migração de banco e sem novas dependências (Python ou frontend).
- Leitura **somente leitura** (`READONLY=TRUE`) pela mesma conexão do serviço
  de pacientes. Tabelas e colunas são constantes, validadas em tempo de execução;
  nada vem de entrada do usuário. Três consultas por atualização (cirurgias,
  procedimentos, suspensões), com cache de 3 minutos.
- Autorização no servidor (`@login_required` + `@require_admin`) em todas as rotas.
- Novos arquivos:
  - `src/services/access_surgery_service.py` e `AccessPatientService.run_read()`;
  - `src/routes/surgery_control.py` e `src/templates/surgery_control/`;
  - `src/static/js/pages/surgery-control.js`, `src/static/css/pages/surgery-control.css`
    e a entrada Vite `surgery-control`;
  - ícone `clipboard-list`.
- **Limitação:** a validação contra um arquivo Access real não foi feita no
  ambiente de desenvolvimento (sem driver/arquivo). Os testes usam conexões
  simuladas. Confirme a tela com o banco do CPAM após atualizar.
