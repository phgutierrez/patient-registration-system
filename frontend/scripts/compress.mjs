// Gera versões .gz (gzip -9) de CSS/JS/SVG estáticos. O Flask as serve com
// "Content-Encoding: gzip" quando o navegador aceita (Waitress não comprime).
import { gzipSync, constants } from 'node:zlib';
import { readdirSync, readFileSync, writeFileSync, statSync, unlinkSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const statik = join(root, 'src', 'static');
const DIRS = ['dist', 'icons', 'vendor/bootstrap'];
const ELIGIBLE = /\.(js|css|svg)$/;

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* walk(path);
    else yield path;
  }
}

let saved = 0;
let count = 0;
for (const dir of DIRS) {
  const base = join(statik, dir);
  if (!existsSync(base)) continue;
  for (const path of walk(base)) {
    if (path.endsWith('.gz')) {
      if (!existsSync(path.slice(0, -3))) unlinkSync(path); // órfão
      continue;
    }
    if (!ELIGIBLE.test(path)) continue;
    const data = readFileSync(path);
    const gz = gzipSync(data, { level: constants.Z_BEST_COMPRESSION });
    gz[9] = 255; // byte de SO fixo: mesma saída no Windows e no Linux
    if (gz.length < data.length * 0.9) {
      writeFileSync(`${path}.gz`, gz);
      saved += data.length - gz.length;
      count += 1;
    } else if (existsSync(`${path}.gz`)) {
      unlinkSync(`${path}.gz`);
    }
  }
}
console.log(`gzip: ${count} arquivos, ${(saved / 1024).toFixed(1)} KB a menos na rede`);
