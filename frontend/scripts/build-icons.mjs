// Gera src/static/icons/icons-<hash>.svg contendo SOMENTE os ícones Lucide
// listados em src/static/icon-map.json, e um manifesto para o Flask.
// Fica fora de dist/ para que os ícones existam mesmo sem os bundles do Vite.
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, readdirSync, unlinkSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const require = createRequire(import.meta.url);
const iconsDir = join(dirname(require.resolve('lucide-static/package.json')), 'icons');
const distDir = join(root, 'src', 'static', 'icons');
const map = JSON.parse(readFileSync(join(root, 'src', 'static', 'icon-map.json'), 'utf8')).icons;

const symbols = Object.keys(map).sort().map((name) => {
  const svg = readFileSync(join(iconsDir, `${name}.svg`), 'utf8');
  const inner = svg
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/^[\s\S]*?<svg[^>]*>/, '')
    .replace(/<\/svg>\s*$/, '')
    .replace(/\s*\n\s*/g, '')
    .trim();
  return `<symbol id="${name}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${inner}</symbol>`;
});

const sprite = `<svg xmlns="http://www.w3.org/2000/svg"><!-- Lucide (ISC) https://lucide.dev -->${symbols.join('')}</svg>\n`;
const hash = createHash('sha256').update(sprite).digest('hex').slice(0, 8);
const file = `icons-${hash}.svg`;

mkdirSync(distDir, { recursive: true });
for (const old of readdirSync(distDir)) {
  if (/^icons-[0-9a-f]{8}\.svg$/.test(old) && old !== file) unlinkSync(join(distDir, old));
}
writeFileSync(join(distDir, file), sprite);
writeFileSync(
  join(distDir, 'icons-manifest.json'),
  `${JSON.stringify({ file, icons: Object.keys(map).sort() }, null, 2)}\n`,
);
console.log(`icons: ${symbols.length} símbolos -> static/icons/${file} (${sprite.length} bytes)`);
