# Notas de versão — 2.9.0 (novembro de 2026)

## Para os usuários

- **Pacientes do dia.** Uma nova tela no menu lateral (e um atalho no Início)
  lista os pacientes agendados **hoje** para o médico logado.
  - Os dados vêm da tabela **Ocorrencias** do banco Access do CPAM, o mesmo
    banco já usado para buscar pacientes por prontuário.
  - O médico é identificado pelo **nome completo do seu cadastro** no sistema,
    comparado com `Nome_medico`. Pequenas diferenças de grafia são aceitas:
    acentos, "Dr./Dra.", "da/de/dos", nome do meio omitido e uma ou outra
    letra trocada.
  - Filtro por turno: **Manhã**, **Tarde** ou **Ambos**, cada um com a contagem.
  - A ordem segue a abertura do prontuário (`quandoreg`), do mais antigo ao
    mais recente, e cada paciente aparece numerado com a sua posição.
  - A lista **sincroniza sozinha a cada 3 minutos**. O botão
    **Sincronizar agora** força a leitura na hora.
- **Clique no nome do paciente** para abrir as ações:
  - **Solicitar cirurgia:**
    - se o paciente já existe no sistema (pelo prontuário), abre direto o pedido;
    - se não existe, o sistema busca os dados no CPAM pelo prontuário,
      **cadastra o paciente automaticamente** e abre o pedido de cirurgia já
      preenchido.
  - **Prontuário:** ainda **não está disponível**. Aparece um aviso de que a
    função está em desenvolvimento.
- **Diagnóstico e CID no pedido de cirurgia.** Os dois campos agora ficam no
  topo de *Dados clínicos*, já preenchidos com o que está no cadastro do
  paciente.
  - Ao gerar a solicitação, eles são gravados no cadastro e saem no PDF.
  - Pacientes importados do CPAM chegam sem diagnóstico e CID. Um aviso pede
    para completá-los.
  - O CID aceita o formato com ponto (ex.: `M16.1` vira `M161`).

## Requisitos

- O Access precisa ter a tabela `Ocorrencias` com as colunas `dt_atend`,
  `Nome_medico` e `prontuario`.
  - `turnomed` e `quandoreg` são usadas quando existem.
  - O nome do paciente vem de `cadastro_de_pacientes`, pelo prontuário.
  - Os nomes das colunas são reconhecidos sem diferenciar maiúsculas de minúsculas.
- O **nome completo** de cada médico no sistema (*Meu perfil*) precisa
  corresponder ao nome usado na agenda do CPAM.

## Técnico

- Sem migração de banco e sem novas dependências Python.
- A leitura do Access continua **somente leitura** (`READONLY=TRUE`).
  - A agenda do dia inteiro, de todos os médicos, fica em cache por 3 minutos
    em cada estação, então cada computador faz no máximo uma consulta a cada 3 minutos.
  - Os nomes são buscados em lote (`IN`, blocos de 100).
- Novos arquivos:
  - `src/routes/today.py` e `src/templates/today/`;
  - `src/static/js/pages/today.js` e `src/static/css/pages/today.css`;
  - entrada Vite `today`.
- A montagem da configuração do Access foi centralizada em `build_access_config()`.
