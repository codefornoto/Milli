import { readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const htmlPath = join(root, 'index.html');
const start = '/* PERSONA_IMAGES_BASE64_START */';
const end = '/* PERSONA_IMAGES_BASE64_END */';

const entries = [];
for (let index = 1; index <= 20; index += 1) {
  const number = String(index).padStart(2, '0');
  const bytes = await readFile(join(root, 'images', `persona${number}.webp`));
  entries.push(`  P${number}: 'data:image/webp;base64,${bytes.toString('base64')}'`);
}

const block = `${start}\nconst PERSONA_IMAGES = Object.freeze({\n${entries.join(',\n')}\n});\n${end}`;
let html = await readFile(htmlPath, 'utf8');
const pattern = new RegExp(`${start.replaceAll('*', '\\*')}[\\s\\S]*?${end.replaceAll('*', '\\*')}`);

if (pattern.test(html)) {
  html = html.replace(pattern, block);
} else {
  html = html.replace('<script>\n', `<script>\n${block}\n`);
}

// The old CSS-only person silhouette was a missing-image fallback. It must not
// remain in the single-file build because it can sit above the embedded art.
html = html
  .replace(/\.portrait-fallback\{[^}]*\}\.portrait-fallback:before\{[^}]*\}\.portrait-fallback:after\{[^}]*\}\.portrait-fallback span\{[^}]*\}/, '')
  .replace(/\.portrait-fallback:before\{[^}]*\}\.portrait-fallback:after\{[^}]*\}/, '');

await writeFile(htmlPath, html);
console.log(`Embedded ${entries.length} persona images into index.html`);
