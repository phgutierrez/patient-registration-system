# Frontend (Vite + HTMX + Alpine.js + Lucide)

O sistema continua sendo Flask + Jinja2 renderizado no servidor. O frontend só
**melhora** páginas que já funcionam sem JavaScript.

## Estrutura

| Caminho | Papel |
|---|---|
| `src/static/js`, `src/static/css` | **Fontes** (editar aqui). Também são o fallback sem build. |
| `frontend/entries/*.js` | Entradas do Vite: importam as fontes da página + HTMX/Alpine quando usados. |
| `frontend/lib/` | HTMX e Alpine (build CSP) importados do `node_modules` (sem CDN). |
| `src/static/icon-map.json` | Ícones Lucide usados (chave) e o nome Font Awesome que substituíram (histórico). |
| `src/static/dist/` | **Gerado** por `npm run build` (versionado no Git). |
| `src/static/icons/` | Sprite Lucide gerado (`icons-<hash>.svg`), fora de `dist` para existir mesmo sem bundles. |
| `*.gz` em `dist`, `icons`, `vendor/bootstrap` | Gerados por `frontend/scripts/compress.mjs`; servidos com `Content-Encoding: gzip`. |
| `src/frontend_assets.py` | Helpers Jinja `vite_css()`, `vite_js()`, `icon()` e cache de `dist`. |
| `src/htmx_utils.py` | `render_page_or_partial()`: mesma rota/URL serve página completa ou fragmento. |

Entradas: `shell`, `patients`, `agenda`, `patient-new`, `patient-edit`,
`surgery-request`, `surgery-confirmation`, `settings`, `procedures`.

Nos templates:

```jinja
{% block page_styles %}{{ vite_css('agenda') }}{% endblock %}
{% block bootstrap_js %}{% include "partials/bootstrap_js.html" %}{% endblock %}  {# só se usar modal/dropdown/collapse #}
{% block page_scripts %}{{ vite_js('agenda') }}{% endblock %}
{{ icon('search', extra_class='me-1') }}   {# <i class="lucide …"><svg class="icon"><use …#search></svg></i> #}
```

## Comandos

```bash
npm ci            # instala versões exatas do package-lock.json
npm run build     # gera src/static/dist (bundles + sprite de ícones)
npm run dev       # rebuild automático (com sourcemaps) ao salvar
npm run measure   # tamanho por página: v2.6 x v2.7 (bruto e gzip)
npm run check     # build + falha se src/static/dist diferir do Git
```

Depois de alterar qualquer arquivo em `src/static/js`, `src/static/css`,
`frontend/` ou `icon-map.json`, rode `npm run build` e **versione `src/static/dist`**.
O build do executável e as atualizações via `git pull` usam esses arquivos sem Node.

## Regras

- Sem SPA. Regras de negócio, validação e permissões ficam no servidor.
- HTMX: requisições que não são GET enviam `X-CSRFToken` (meta `csrf-token`).
  `historyCacheSize = 0` evita guardar HTML com dados clínicos no navegador.
- Resposta parcial apenas com `HX-Request: true`. Restauração de histórico e
  navegação sem JS recebem a página completa (`Vary: HX-Request`).
- Sem `<script>` inline, `onclick`, `onsubmit` ou `style=""` nos templates
  (verificado por teste). A CSP é aplicada; estilos vão para CSS (veja os
  utilitários `.u-*` em `app-shell.css`). Em JS, use `element.style`/classes,
  nunca `style="..."` dentro de `innerHTML`. Use `data-confirm`, `data-action="shutdown"` e
  `data-toggle-panel="id"`, tratados em `app-shell.js`.
- Alpine usa o build CSP: componentes registrados com `Alpine.data()` e
  expressões simples (propriedades/getters).
- Não use `innerHTML` com dados do servidor sem escapar (`textContent` ou `escapeHtml`).
- Novos ícones: adicione o nome Lucide em `icon-map.json` e rode o build. Em
  JavaScript, use `window.appIcon('nome', 'classes')`.
- Teste de navegador: `pip install -r requirements-e2e.txt`,
  `python -m playwright install chromium` e
  `python -m pytest tests/test_browser_e2e.py`.
