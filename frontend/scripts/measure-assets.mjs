// Mede bytes (bruto e gzip) de CSS/JS/ícones carregados por página:
// "antes" = v2.6 (arquivos-fonte + Bootstrap JS global) e "depois" = bundles v2.7.
// Uso: npm run measure
import { gzipSync } from 'node:zlib';
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const statik = join(root, 'src', 'static');
const dist = join(statik, 'dist');
const manifest = JSON.parse(readFileSync(join(dist, '.vite', 'manifest.json'), 'utf8'));
const icons = JSON.parse(readFileSync(join(dist, 'icons-manifest.json'), 'utf8'));

const COMMON = ['vendor/bootstrap/bootstrap.min.css', 'vendor/fontawesome/css/all.min.css',
  'vendor/fontawesome/webfonts/fa-solid-900.woff2'];
const BOOTSTRAP_JS = 'vendor/bootstrap/bootstrap.bundle.min.js';
const OLD_SHELL = ['css/app-shell.css', 'css/sync-status.css', 'js/app-shell.js', 'js/sync-status.js', 'js/lifecycle.js'];

// página -> [entrada Vite, usa Bootstrap JS?, arquivos v2.6 da página]
const PAGES = {
  'Início': [null, false, ['css/pages/home.css', 'js/pages/home.js']],
  'Pacientes': ['patients', true, ['css/pages/patients.css', 'js/pages/patients.js']],
  'Agenda': ['agenda', true, ['css/pages/agenda.css', 'js/pages/agenda.js']],
  'Novo paciente': ['patient-new', false, ['css/pages/patient-new.css', 'js/pages/patient-new.js']],
  'Solicitação de cirurgia': ['surgery-request', true, ['css/pages/surgery-request.css', 'js/pages/surgery-request.js']],
  'Confirmação': ['surgery-confirmation', true, []],
  'Configurações': ['settings', true, []],
  'Procedimentos': ['procedures', true, ['css/pages/procedures.css', 'js/pages/procedures.js']],
};

const size = (path) => {
  if (!existsSync(path)) return [0, 0];
  const data = readFileSync(path);
  return [data.length, gzipSync(data, { level: 9 }).length];
};
const sum = (paths) => paths.reduce((acc, p) => { const [r, g] = size(p); return [acc[0] + r, acc[1] + g]; }, [0, 0]);

function entryFiles(name, seen = new Set()) {
  const key = name.startsWith('_') ? name : `frontend/entries/${name}.js`;
  if (seen.has(key) || !manifest[key]) return [];
  seen.add(key);
  const chunk = manifest[key];
  return [...(chunk.imports || []).flatMap((i) => entryFiles(i, seen)), chunk.file, ...(chunk.css || [])]
    .map((f) => (f.startsWith('/') ? f : join(dist, f)));
}

const kb = ([r, g]) => `${(r / 1024).toFixed(1)} KB (${(g / 1024).toFixed(1)} KB gz)`;
const rows = [];
for (const [page, [entry, usesBootstrap, oldPage]] of Object.entries(PAGES)) {
  const before = sum([...COMMON, BOOTSTRAP_JS, ...OLD_SHELL, ...oldPage].map((p) => join(statik, p)));
  const after = sum([
    ...COMMON.map((p) => join(statik, p)),
    ...(usesBootstrap ? [join(statik, BOOTSTRAP_JS)] : []),
    ...entryFiles('shell'),
    join(dist, icons.file),
    ...(entry ? entryFiles(entry) : oldPage.map((p) => join(statik, p))),
  ]);
  rows.push({ page, before: kb(before), after: kb(after), delta: `${(((after[1] - before[1]) / before[1]) * 100).toFixed(0)}% gz` });
}
console.table(rows);
console.log('Observações: páginas de Confirmação/Configurações tinham script/estilo inline (não contados em "antes").');
console.log('HTMX (pacientes/agenda) e Alpine (configurações) são carregados só onde usados.');
