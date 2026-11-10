# Changelog — v2.7.0

Data: novembro de 2026

Sem migração de banco, sem mudança de regras de negócio, permissões ou
sincronização. Atualização: [ATUALIZACAO_V2.7.md](ATUALIZACAO_V2.7.md).

## Documentos PDF

- **Faixa "RESERVAR VAGA DE UTI"** no PDF de internação, página "AVISO DE
  CIRURGIA", logo abaixo de "DATA DA INTERNAÇÃO", quando a solicitação marca
  *Reserva de Vaga UTI*. Fundo verde-claro, texto preto em negrito no mesmo
  tamanho do título "AVISO DE CIRURGIA" (15,96 pt).
  - A informação fica no snapshot do documento (`__ReservaUTI`), então a
    regeneração é fiel; snapshots antigos não ganham a faixa.
- **Requisição de hemocomponente**: o modelo trazia a data de exemplo
  `03/05/2024` gravada no campo `DATA`. Quando o valor ficava vazio, essa data
  reaparecia no PDF final. O renderizador agora zera de fato campos de texto
  vazios. O campo é sempre preenchido com a **data de internação**.
  O nome do hospital, que também vinha do modelo, passou a ser preenchido
  explicitamente (saída idêntica).

## Interface (modernização incremental, sem SPA)

- **Vite** empacota CSS/JS em `src/static/dist` (nomes com hash, minificação,
  sourcemap só em desenvolvimento). Os bundles são versionados no repositório;
  Node.js só é necessário para quem altera o frontend.
- Fallback: sem `src/static/dist`, o Flask carrega os arquivos-fonte de
  `src/static/css` e `src/static/js` automaticamente.
- **HTMX** (local, sem CDN):
  - **Pacientes**: busca com debounce, paginação e contador atualizados sem
    recarregar a página. A busca continua no servidor, com prioridade do
    prontuário exato e 20 itens por página.
  - **Agenda**: navegação de período, Semana/Mês, filtros e "Atualizar agora"
    trocam só a área da agenda. Os links de período agora são calculados no
    servidor; isso corrige o deslocamento de data (UTC) após as 21h.
  - Sem HTMX, links e formulários funcionam como antes (GET tradicional).
- **Alpine.js** (build CSP, sem `eval`): alternância Rede/Local do Access nas
  Configurações.
- **Ícones Lucide** (sprite SVG local) no menu lateral, nas mensagens, em
  Pacientes e na Agenda. O Font Awesome continua nas demais telas.
- **Bootstrap JS** passou a ser carregado só nas páginas que usam modal,
  dropdown ou accordion.
- Todos os scripts e estilos inline foram removidos dos templates (`onclick`,
  `onsubmit`, `<script>`). A CSP (report-only) não permite mais
  `'unsafe-inline'` em `script-src`.
- Arquivos com hash em `/static/dist` recebem cache de 1 ano (`immutable`).

## Correções

- Botão de menu (☰) não aparecia em telas ≤ 768 px: a regra base escondia o
  botão depois da media query.
- Mensagens flash apareciam duplicadas na página de Configurações.
- Mensagens da categoria `danger` agora usam o estilo de erro.
- O link "Histórico Sync" agora marca `aria-current` quando ativo.

## Segurança e dependências

- `Werkzeug` 3.1.8 → **3.1.9** (CVE-2026-102598).
- `requirements-dev.txt` (pytest) para rodar a suíte.

## Build e testes

- `build_exe_32bits.py` (versão `2.7.0`) inclui `src/static/dist` e
  `icon-map.json`, valida os manifestos antes do build e confere os arquivos no
  `_internal` depois.
- Novos testes:
  - `test_htmx_partials.py`: parciais, fallback, CSRF, permissões, agenda
    stale/erro/sem configuração, busca e paginação.
  - `test_frontend_assets.py`: manifesto, fallback, cache, CSP, CDN e ícones.
  - Faixa de UTI e data do hemocomponente em `test_pdf_generation.py`.
