import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import { load } from 'cheerio';
import { generateData, siteRoot } from './build-data.mjs';
const personal = JSON.parse(await readFile(resolve(siteRoot, 'content/personal.json'), 'utf8'));

export function checkRendered(html, { story, charts }) {
  const $ = load(html);
  const checked = new Set();
  $('[data-number]').each((_, element) => {
    const key = $(element).attr('data-number');
    assert.ok(story.registry[key], `Unregistered number: ${key}`);
    assert.equal($(element).text(), story.registry[key].text, `Displayed value mismatch: ${key}`);
    checked.add(key);
  });
  const canonical = svg => load(svg, { xmlMode: true }).html().replace(/\s+/g, ' ').trim();
  const plots = new Set();
  $('[data-plot]').each((_, element) => {
    const key = $(element).attr('data-plot');
    assert.ok(charts[key], `Unregistered plot: ${key}`);
    assert.equal(canonical($(element).html()), canonical(charts[key]), `Displayed chart mismatch: ${key}`);
    plots.add(key);
  });
  assert.equal(plots.size, Object.keys(charts).length, 'Every generated chart must be displayed');
  for (const key of ['brand.0.rate', 'brand.1.rate', 'brand.2.rate', 'comparison.0.raw', 'comparison.1.raw', 'comparison.shrinkRange', 'ml.0.mae', 'ml.1.mae', 'ml.2.mae', 'ml.n', 'coverage.rate']) assert.ok(checked.has(key), `Missing headline: ${key}`);
  const walk = element => {
    for (const node of element.children || []) {
      if (node.type === 'text' && /\d/.test(node.data)) {
        const parent = $(node.parent);
        assert.ok(parent.closest('[data-number],[data-plot],[data-decoration="section"],[data-definition="top10"]').length, `Unverified numeric text: ${node.data.trim()}`);
      } else if (node.type !== 'script' && node.type !== 'style' && node.name !== 'script' && node.name !== 'style') walk(node);
    }
  };
  $('main,body > footer').each((_, node) => walk(node));
  $('[data-definition="top10"]').each((_, node) => assert.deepEqual($(node).text().match(/\d+/g), ['10'], 'Top-10 definition drift'));
  assert.equal($('h1').text().replace(/\s+/g, ' ').trim().replace('WANTEDTO', 'WANTED TO').replace('ANIKE', 'A NIKE'), story.copy.hero);
  assert.equal($('meta[name="description"]').attr('content'), story.copy.subhead);
  assert.equal(new URL($('meta[property="og:image"]').attr('content'), 'http://localhost:3000').pathname, '/share.png');
  assert.equal($('main section').length, 7);
  assert.equal($('.hero img,.hero picture').length, 0, 'Hero must remain a black headline with no photograph');
  const pick = $('section[aria-labelledby="pick-title"]');
  assert.equal(pick.find('[data-number="comparison.shrinkRange"]').closest('details').length, 0, 'Shrinkage headline must be visible');
  for (const name of ['comparison.0.raw', 'comparison.1.raw']) assert.equal(pick.find(`[data-number="${name}"]`).closest('details').find('summary').text(), 'Sample counts and the README finding', 'Unadjusted averages belong in the sample disclosure');
  assert.equal(pick.find('.takeaway').nextAll('.comparison-grid').length, 1, 'Shrinkage must lead the adjusted charts');
  assert.equal($('.personal-story').text(), personal.paragraph, 'Personal story must retain the author’s exact words');
  assert.equal($('.commit-image').attr('alt'), personal.alt);
  assert.equal($('.commit-figure figcaption').text(), personal.caption);
  assert.equal($('.commit-image').attr('width'), '1638');
  assert.equal($('.commit-image').attr('height'), '2048');
  assert.equal($('.commit-figure source[type="image/avif"]').length, 1);
  assert.equal($('.commit-figure source[type="image/webp"]').length, 1);
  assert.equal($('.personal-copy blockquote').length, 1, 'Bowerman quote follows the personal paragraph');
  assert.ok($('body').text().includes('Independent student project by Alexandra Cowan. Not affiliated with or endorsed by Nike, Inc.'));
  return { checked: checked.size, charts: plots.size };
}

async function main() {
  const data = await generateData();
  for (const [name, value] of Object.entries(data)) assert.equal(await readFile(resolve(siteRoot, 'data', `${name}.json`), 'utf8'), JSON.stringify(value, null, 2) + '\n', `Stale ${name}.json`);
  const result = checkRendered(await readFile(resolve(siteRoot, 'out/index.html'), 'utf8'), data);
  console.log(`PASS: ${result.checked} rendered, sourced values and ${result.charts} charts; no unverified numeric text.`);
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
