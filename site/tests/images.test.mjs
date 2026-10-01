import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import sharp from 'sharp';
import { siteRoot } from '../scripts/build-data.mjs';
const image = JSON.parse(await readFile(resolve(siteRoot, 'data/image.json'), 'utf8'));
test('publication preserves the original commitment graphic and uncropped responsive formats', async () => {
  const bytes = await readFile(resolve(siteRoot, `public${image.original.src}`));
  assert.equal(createHash('sha256').update(bytes).digest('hex'), image.original.sha256);
  const original = await sharp(bytes).metadata();
  assert.equal(original.width, image.original.width);
  assert.equal(original.height, image.original.height);
  assert.equal(image.variants.length, 8);
  for (const variant of image.variants) {
    const actual = await sharp(resolve(siteRoot, `public${variant.src}`)).metadata();
    assert.equal(actual.format, variant.format === 'avif' ? 'heif' : variant.format);
    assert.equal(actual.width, variant.width);
    assert.equal(actual.height, variant.height);
    assert.ok(Math.abs(actual.height - actual.width * original.height / original.width) <= 1, 'Resizing must retain the portrait aspect ratio within raster rounding');
  }
});
