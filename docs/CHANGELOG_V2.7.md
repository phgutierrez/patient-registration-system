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
- **Ícones Lucide** (sprite SVG local em `src/static/icons`, 87 ícones) em
  todas as telas. O **Font Awesome foi removido** (−397 KB), e o layout de
  cada tela foi mantido.
- **Bootstrap JS** passou a ser carregado só nas páginas que usam modal,
  dropdown ou accordion.
- Todos os scripts e estilos inline foram removidos dos templates (`onclick`,
  `onsubmit`, `<script>`, `style=""`).
- A **CSP agora é aplicada** (`Content-Security-Policy`, sem `'unsafe-inline'`
  em `script-src` e `style-src`, sem fontes externas).
  - `SECURITY_CSP_ENFORCE=false` no `.env` volta ao modo somente relatório.
- Arquivos CSS/JS/SVG estáticos têm versão **`.gz` pré-comprimida**, servida
  quando o navegador aceita gzip (o Waitress não comprime). São cerca de
  416 KB a menos na rede.
- Arquivos com hash em `/static/dist` recebem cache de 1 ano (`immutable`).

## Correções

- Botão de menu (☰) não aparecia em telas ≤ 768 px: a regra base escondia o
  botão depois da media query.
- Mensagens flash apareciam duplicadas na página de Configurações.
- Modais de edição de procedimento estavam dentro de `<tbody>` (HTML inválido)
  e ganharam rótulos acessíveis.
- Mensagens da categoria `danger` agora usam o estilo de erro.
- O link "Histórico Sync" agora marca `aria-current` quando ativo.

## Segurança e dependências

- `Werkzeug` 3.1.8 → **3.1.9** (CVE-2026-102598).
- `requirements-dev.txt` (pytest) para rodar a suíte.

## Limpeza

- Removidos templates sem rota (`login.html`, `auth/login.html`,
  `registration.html`, `patient_details.html`, `select_specialty.html`,
  `surgery/download.html`, `surgery_request.html`).
- Removido o `src/routes.py` legado, que estava quebrado e era sombreado pelo
  pacote `src/routes/`.
- Removidos os PDFs de teste esquecidos em `src/static/pdfs/gerados`.

## Build e testes

- `build_exe_32bits.py` (versão `2.7.0`) inclui `src/static/dist`, `src/static/icons` e
  `icon-map.json`, valida os manifestos antes do build e confere os arquivos no
  `_internal` depois.
- Novos testes:
  - `test_htmx_partials.py`: parciais, fallback, CSRF, permissões, agenda
    stale/erro/sem configuração, busca e paginação.
  - `test_frontend_assets.py`: manifesto, fallback, cache, CSP, CDN e ícones.
  - Faixa de UTI e data do hemocomponente em `test_pdf_generation.py`.
  - `test_browser_e2e.py` (opcional, Playwright/Chromium,
    `requirements-e2e.txt`): navegação real com CSRF e CSP aplicada em todas
    as páginas. Falha com qualquer erro de JS, violação de CSP ou requisição
    externa.
