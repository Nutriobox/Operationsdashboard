// Next.js `output: 'standalone'` does not include public/ or .next/static/
// in the standalone bundle. We have to copy them ourselves so that
// `node .next/standalone/server.js` can serve images, fonts, and JS chunks.
// Runs automatically after `next build` via the postbuild npm script.
import { cpSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const root = process.cwd();
const standaloneDir = resolve(root, '.next', 'standalone');

if (!existsSync(standaloneDir)) {
  console.log(
    '[copy-standalone-assets] .next/standalone not found — assuming non-standalone build, skipping copy.'
  );
  process.exit(0);
}

const publicSrc = resolve(root, 'public');
if (existsSync(publicSrc)) {
  cpSync(publicSrc, resolve(standaloneDir, 'public'), { recursive: true });
  console.log('[copy-standalone-assets] copied public/ -> .next/standalone/public/');
}

const staticSrc = resolve(root, '.next', 'static');
if (existsSync(staticSrc)) {
  cpSync(staticSrc, resolve(standaloneDir, '.next', 'static'), { recursive: true });
  console.log('[copy-standalone-assets] copied .next/static/ -> .next/standalone/.next/static/');
}
