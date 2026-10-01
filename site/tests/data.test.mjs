import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { generateData, siteRoot } from '../scripts/build-data.mjs';
import { checkRendered } from '../scripts/check-rendered.mjs';

const generated = await generateData();
test('committed JSON exactly reconciles with pipeline files and README ledger', async () => {
  for (const [name, data] of Object.entries(generated)) assert.equal(await readFile(join(siteRoot, 'data', `${name}.json`), 'utf8'), JSON.stringify(data, null, 2) + '\n');
});
test('switch slots retain missing outcomes and minimum pre/post evidence', () => {
  for (const event of generated.story.cases) {
    assert.equal(event.points.length, 5);
    assert.ok(event.points.some(d => d.relative < 0 && d.value !== null));
    assert.ok(event.points.some(d => d.relative >= 0 && d.value !== null));
    assert.ok(event.points.filter(d => d.season === '2019-20').every(d => d.value === null));
  }
  const washington = generated.story.cases.find(d => d.school === 'Washington');
  assert.equal(washington.points.find(d => d.relative === 0).value, null);
  const index = generated.story.cases.indexOf(washington);
  const svg = generated.charts[`case-${index}`];
  const linePath = svg.match(/aria-label="line"[^]*?<path[^]*?d="([^"]+)"/);
  assert.ok(linePath && linePath[1].split('M').length >= 3, 'Path must have multiple segments across COVID gap');
});
test('headline and CI use different, correctly labeled raw/matched samples', () => {
  const { comparisons, registry } = generated.story;
  for (let i = 0; i < comparisons.length; i++) {
    assert.notEqual(comparisons[i].meanGap, comparisons[i].estimates[0].value);
    assert.ok(comparisons[i].estimates.every(d => d.low <= 0 && d.high >= 0));
    assert.ok(registry[`comparison.${i}.raw`].sample.includes('unadjusted'));
  }
});
test('changing a README number causes source reconciliation to fail', async () => {
  const root = await mkdtemp(join(tmpdir(), 'swoosh-site-mutation-'));
  try {
    for (const path of Object.keys(generated.provenance.sources)) {
      const out = join(root, path); await mkdir(dirname(out), { recursive: true });
      let data = await readFile(join(siteRoot, '..', path));
      if (path === 'README.md') data = Buffer.from(data.toString().replace(generated.story.registry['brand.0.rate'].text, '99.9%'));
      await writeFile(out, data);
    }
    await assert.rejects(generateData(root), /README brand number mismatch/);
  } finally { await rm(root, { recursive: true, force: true }); }
});
test('render gate rejects wrong numbers, extra numeric prose and changed chart marks', async t => {
  if (process.env.SITE_SOURCE_ONLY === '1') { t.skip('Rendered checks run after the new static export'); return; }
  let html;
  try { html = await readFile(join(siteRoot, 'out/index.html'), 'utf8'); }
  catch { t.skip('Static HTML is checked after next build by check-numbers'); return; }
  assert.ok(checkRendered(html, generated).checked > 50);
  const correct = generated.story.registry['brand.0.rate'].text;
  assert.throws(() => checkRendered(html.replace(`>${correct}</span>`, '>99.9%</span>'), generated), /Displayed value mismatch/);
  assert.throws(() => checkRendered(html.replace('</main>', '<p>999 unverified outcomes</p></main>'), generated), /Unverified numeric text/);
  assert.throws(() => checkRendered(html.replace('fill="#E9533A"', 'fill="#123456"'), generated), /Displayed chart mismatch/);
});
