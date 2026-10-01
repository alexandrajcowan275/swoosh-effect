import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import sharp from 'sharp';

const siteRoot = fileURLToPath(new URL('../', import.meta.url));
const originalPath = resolve(siteRoot, 'public/images/usc-commit.jpg');
const bytes = await readFile(originalPath);
const metadata = await sharp(bytes).metadata();
assert.equal(metadata.width, 1638, 'Use the original full-resolution USC graphic');
assert.equal(metadata.height, 2048, 'Use the original full-resolution USC graphic');
assert.ok(!metadata.orientation || metadata.orientation === 1, 'Unexpected orientation: review before publishing');
const original = { src: '/images/usc-commit.jpg', width: metadata.width, height: metadata.height, sha256: createHash('sha256').update(bytes).digest('hex') };
const variants = [];
for (const width of [400, 800, 1200, original.width]) {
  for (const format of ['webp', 'avif']) {
    // Width-only resizing preserves the entire composition. No crop, rotation,
    // retouching or color adjustment; metadata is stripped only on derivatives.
    const src = `/images/usc-commit-${width}.${format}`;
    const { data, info } = await sharp(bytes).resize({ width, withoutEnlargement: true })[format]({ quality: format === 'webp' ? 82 : 60, effort: 6 }).toBuffer({ resolveWithObject: true });
    await writeFile(resolve(siteRoot, `public${src}`), data);
    variants.push({ src, format, width: info.width, height: info.height });
  }
}
await writeFile(resolve(siteRoot, 'data/image.json'), JSON.stringify({ original, variants }, null, 2) + '\n');
assert.equal(createHash('sha256').update(await readFile(originalPath)).digest('hex'), original.sha256, 'Original image must remain unchanged');
console.log(`PASS: ${variants.length} uncropped responsive WebP/AVIF images; original ${original.width}×${original.height} preserved.`);
