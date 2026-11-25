# Notas de versão — 3.0.1 (novembro de 2026)

Correção da tela **Controle de Cirurgias**, que ficava girando e podia derrubar a
conexão quando o banco Access era grande e estava na pasta compartilhada (modo rede).

## Para os usuários

- **A tela não espera mais o Access.** Ela abre na hora:
  - na primeira vez (ou após reiniciar o sistema) mostra *Carregando as cirurgias…*
    com a etapa em andamento e o tempo decorrido. A leitura continua em segundo
    plano, você pode usar outras telas e esta se atualiza sozinha quando termina;
  - depois, mostra sempre a última leitura. Se ela tiver mais de 5 minutos, uma
    atualização começa sozinha em segundo plano e os dados trocam quando chegam.
- **Atualizar agora** (antes "Sincronizar agora") pede uma nova leitura em segundo plano.
  Se der erro, aparece a orientação e o botão **Tentar novamente**; os dados
  anteriores continuam visíveis quando existirem.
- **Carga menor e mais rápida.** Por padrão são lidos os **últimos 12 meses** e
  todo o futuro, só de ortopedia. Ao navegar para um mês mais antigo, o sistema
  carrega esse período em blocos de 6 meses, em segundo plano.
- **Sem data programada:** passam a considerar apenas cirurgias **cadastradas nos
  últimos 12 meses** (o aviso informa o mês de início).
- **Outras telas não travam mais.** Pacientes do dia e a busca por prontuário
  continuam respondendo enquanto o controle de cirurgias carrega.

## Técnico

- Sem migração de banco e sem novas dependências.
- O Access é lido por uma **conexão própria** (`READONLY=TRUE`, tempo limite de 120 s
  por consulta), sem segurar o lock compartilhado do serviço de pacientes.
- Consultas filtradas e parametrizadas:
  - cirurgias: `dt_prov_CIR >= ?` e `InStr(1, [especialidade_cons], 'ortop', 1) > 0`;
  - registro do bloco: `Data_da_Cirurgia >= ?` e `InStr(1, [Especialidade], 'ortop', 1) > 0`;
  - procedimentos: só os códigos usados (`IN`, blocos de 100), com cache de 24 h;
  - leitura em lotes de 500 linhas, teto de 20.000 por consulta (aviso se atingido).
- **Cópia local do banco (modo rede).** O arquivo `.accdb` da pasta compartilhada é
  copiado em blocos para `instance\access_cache\` e a leitura usa a cópia (mais
  rápida que ler pela rede). A cópia só é refeita se o arquivo mudou **e** a última
  tem mais de 10 minutos (ou ao clicar em *Atualizar agora*). O arquivo original
  nunca é alterado. Se a cópia ou a leitura dela falhar, a leitura segue direto
  pela rede e a tela avisa.
- Variáveis de ambiente opcionais (no `.env`):

  | Variável | Padrão | Efeito |
  |---|---|---|
  | `SURGERY_LOCAL_COPY` | `1` | `0` desliga a cópia local |
  | `SURGERY_LOCAL_COPY_MAX_MB` | `500` | acima disso lê direto pela rede |
  | `SURGERY_LOCAL_COPY_MIN_MINUTES` | `10` | intervalo mínimo entre cópias |
  | `SURGERY_HISTORY_MONTHS` | `12` | meses de histórico carregados por padrão |

- Novos arquivos: `src/services/access_local_copy.py` e
  `src/templates/surgery_control/_loading.html`. A rota `POST /controle-cirurgias/atualizar`
  substitui o antigo `?sync=1` por GET.
- O log registra, por etapa, o número de linhas e os segundos (`Cirurgias etapa=...`)
  e o tempo da cópia local, **sem dados de pacientes**.

## Limitações

- Sem um Access real no ambiente de desenvolvimento, o ganho de velocidade **não foi
  medido**; os testes usam conexões simuladas. Se a carga inicial ainda demorar,
  envie as linhas `Cirurgias etapa=` e `Cópia local do Access` do log para calibrar.
- Sem índice em `dt_prov_CIR`, o Access varre a tabela inteira mesmo com filtro; a
  cópia local e a leitura em segundo plano existem para compensar isso.
