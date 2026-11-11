// Empacota CSS/JS próprios + HTMX + Alpine em src/static/dist (servido pelo
// Flask em /static/dist e incluído no executável PyInstaller).
// As fontes continuam em src/static/js e src/static/css: o Flask volta a
// carregá-las diretamente se o manifesto do Vite não existir (fallback).
import { defineConfig } from 'vite';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const entry = (name) => resolve(root, 'frontend/entries', `${name}.js`);

export const ENTRIES = [
  'shell',
  'patients',
  'agenda',
  'patient-new',
  'patient-edit',
  'surgery-request',
  'surgery-confirmation',
  'settings',
  'procedures',
  'pending',
];

export default defineConfig(({ mode }) => ({
  root,
  base: './',
  publicDir: false,
  logLevel: 'warn',
  build: {
    outDir: 'src/static/dist',
    emptyOutDir: true,
    manifest: true,
    sourcemap: mode === 'development',
    minify: mode !== 'development',
    // Mesmo piso dos scripts atuais (optional chaining): Chrome/Edge 80+.
    target: ['chrome80', 'edge80', 'firefox78', 'safari14'],
    cssCodeSplit: true,
    reportCompressedSize: true,
    modulePreload: { polyfill: false },
    rollupOptions: {
      input: Object.fromEntries(ENTRIES.map((name) => [name, entry(name)])),
      output: {
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
}));
