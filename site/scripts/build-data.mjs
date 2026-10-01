import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { parse } from 'csv-parse/sync';
import { generateCharts } from './charts.mjs';

export const siteRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = resolve(siteRoot, '..');
const tolerance = 1e-9;
const close = (a, b) => assert.ok(Math.abs(a - b) <= tolerance, `${a} != ${b}`);
export const format = (value, digits = 0) => Number(value).toFixed(digits);
const truth = value => String(value).toLowerCase() === 'true';
const plain = value => value.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/\*\*/g, '').trim();

export async function generateData(root = repoRoot) {
  const sources = {};
  const read = async path => {
    const bytes = await readFile(resolve(root, path));
    sources[path] = createHash('sha256').update(bytes).digest('hex');
    return bytes.toString('utf8');
  };
  const csv = async path => parse(await read(path), { columns: true, skip_empty_lines: true });
  const [readme, brandsRaw, panel, coefficientRows, attenuation, metrics, importance, metadataText, validationText, events, confounders, samples, paired, ledger] = await Promise.all([
    read('README.md'), csv('reports/brand_summary.csv'), csv('exports/tableau/school_season.csv'),
    csv('reports/model_coefficients.csv'), csv('reports/lag_attenuation.csv'), csv('reports/ml/metrics.csv'),
    csv('reports/ml/permutation_importance.csv'), read('reports/ml/metadata.json'), read('reports/database_validation.json'),
    csv('exports/tableau/switch_events.csv'), csv('reports/switch_case_confounders.csv'),
    csv('reports/ml/sample_counts.csv'), csv('reports/ml/paired_comparisons.csv'), csv('docs/readme_number_ledger.csv'),
  ]);
  const metadata = JSON.parse(metadataText);
  const validation = JSON.parse(validationText);
  const registry = {};
  const stat = (key, raw, text, source, sample) => {
    registry[key] = { raw, text: String(text), source, sample };
    return raw;
  };
  const headlineSample = 'A+B';
  const brands = ['Nike', 'Under Armour', 'adidas'].map((brand, i) => {
    const row = brandsRaw.find(d => d.evidence_tiers === headlineSample && d.brand === brand);
    assert.ok(row, `Missing ${brand}`);
    const included = panel.filter(d => truth(d.sensitivity_included) && d.brand === brand);
    assert.equal(included.length, +row.n_school_seasons);
    const finishes = included.reduce((n, d) => n + (+d.top10), 0);
    assert.equal(finishes, +row.top10_finishes);
    included.forEach(d => assert.equal(+d.top10, d.rank !== '' && +d.rank <= 10 ? 1 : 0));
    const rate = 100 * finishes / included.length;
    stat(`brand.${i}.rate`, rate, `${format(rate, 1)}%`, 'reports/brand_summary.csv', headlineSample);
    stat(`brand.${i}.n`, included.length, included.length, 'reports/brand_summary.csv', headlineSample);
    stat(`brand.${i}.finishes`, finishes, finishes, 'reports/brand_summary.csv', headlineSample);
    return { brand, n: included.length, finishes, rate, mean: +row.mean_percentile, color: brand === 'Nike' ? '#E9533A' : i === 1 ? '#767676' : '#888888' };
  });
  const comparisons = ['adidas', 'Under Armour'].map((brand, i) => {
    const row = attenuation.find(d => d.Evidence === headlineSample && d['Brand versus Nike'] === brand);
    const meanGap = brands[0].mean - brands.find(d => d.brand === brand).mean;
    const estimates = ['plain_matched', 'lagged'].map((model, j) => {
      const d = coefficientRows.find(d => d.evidence_tiers === headlineSample && d.model === model && d.brand === brand);
      assert.ok(d);
      const n = +d.n;
      const value = -Number(d.coefficient), low = -Number(d.ci_high), high = -Number(d.ci_low);
      const key = `comparison.${i}.${j}`;
      stat(`${key}.estimate`, value, format(value, 2), 'reports/model_coefficients.csv', 'A+B; same matched regression rows');
      stat(`${key}.low`, low, format(low, 2), 'reports/model_coefficients.csv', 'A+B; 95% confidence interval');
      stat(`${key}.high`, high, format(high, 2), 'reports/model_coefficients.csv', 'A+B; 95% confidence interval');
      return { model, label: model === 'lagged' ? 'With last season' : 'Without last season', value, low, high, n, color: model === 'lagged' ? '#E9533A' : '#B8B8B8' };
    });
    assert.equal(estimates[0].n, estimates[1].n);
    close(-estimates[0].value, +row['Plain, matched rows']);
    close(-estimates[1].value, +row['Lagged, same rows']);
    const shrinkage = 100 * (1 - Math.abs(estimates[1].value) / Math.abs(estimates[0].value));
    close(shrinkage, +row['Magnitude shrinkage %']);
    stat(`comparison.${i}.raw`, meanGap, format(meanGap, 2), 'reports/brand_summary.csv', headlineSample + '; unadjusted mean gap');
    stat(`comparison.${i}.shrinkage`, shrinkage, `${format(shrinkage)}%`, 'reports/lag_attenuation.csv', 'A+B; matched model sample');
    return { brand, meanGap, estimates, shrinkage };
  });
  const shrinkRange = `${format(Math.min(...comparisons.map(d => d.shrinkage)))}–${format(Math.max(...comparisons.map(d => d.shrinkage)))}%`;
  stat('comparison.shrinkRange', comparisons.map(d => d.shrinkage), shrinkRange, 'reports/lag_attenuation.csv', 'A+B; matched rows');
  const matchedN = comparisons[0].estimates[0].n;
  stat('comparison.n', matchedN, matchedN, 'reports/model_coefficients.csv', 'A+B; matched rows');
  const modelSample = JSON.parse(coefficientRows.find(d => d.evidence_tiers === headlineSample && d.model === 'lagged').n_per_brand);
  const sampleText = Object.entries(modelSample).map(([brand, n]) => `${brand} ${n}`).join('; ');
  stat('comparison.perBrand', modelSample, sampleText, 'reports/model_coefficients.csv', 'A+B; matched rows');
  stat('confidence', 95, '95%', 'docs/methodology.md', 'confidence interval definition');
  const featureRows = importance.filter(d => d.level === 'individual').sort((a, b) => +a.rank - +b.rank);
  const featureLabel = featureName => featureName === 'points_pctile_lag1' ? 'Last season’s percentile' : featureName === 'points_pctile_lag2' ? 'Two seasons ago' : featureName.replace('sport_lag1__', '').replaceAll('_', ' ').replace('women s', 'Women’s').replace('men s', 'Men’s');
  const features = featureRows.slice(0, 10).map((d, i) => {
    stat(`feature.${i}.rank`, +d.rank, d.rank, 'reports/ml/permutation_importance.csv', 'individual; all-school holdout');
    stat(`feature.${i}.importance`, +d.mean_mae_increase, format(d.mean_mae_increase, 3), 'reports/ml/permutation_importance.csv', 'individual; all-school holdout');
    return { feature: d.feature, label: featureLabel(d.feature), importance: +d.mean_mae_increase, rank: +d.rank };
  });
  assert.equal(features[0].feature, 'points_pctile_lag1');
  stat('ml.featureCount', featureRows.length, featureRows.length, 'reports/ml/permutation_importance.csv', 'individual');
  const modelLabels = { naive: 'Same as last season', lagged_ols: 'Lagged OLS', lightgbm: 'LightGBM' };
  const brandImportance = +featureRows.find(d => d.feature === 'brand').mean_mae_increase;
  stat('ml.brandImportance', brandImportance, brandImportance === 0 ? 'zero' : format(brandImportance, 3), 'reports/ml/permutation_importance.csv', 'individual; heavily masked brand input');
  const models = Object.entries(modelLabels).map(([model, label], i) => {
    const mae = metrics.find(d => d.season === 'pooled' && d.model === model && d.metric === 'MAE');
    const rmse = metrics.find(d => d.season === 'pooled' && d.model === model && d.metric === 'RMSE');
    assert.equal(+mae.n, metadata.n_test);
    for (const [field, raw] of [['mae', +mae.estimate], ['low', +mae.ci_low], ['high', +mae.ci_high], ['rmse', +rmse.estimate]]) {
      stat(`ml.${i}.${field}`, raw, format(raw, 2), 'reports/ml/metrics.csv', 'pooled; all-school holdout; pre-season A/B brand only');
    }
    if (model !== 'naive') {
      const diff = paired.find(d => d.season === 'pooled' && d.model === model && d.reference === 'naive' && d.metric === 'MAE');
      assert.ok(+diff.ci_low <= 0 && +diff.ci_high >= 0, 'MAE takeaway must be revisited');
    }
    return { model, label, mae: +mae.estimate, low: +mae.ci_low, high: +mae.ci_high, rmse: +rmse.estimate };
  });
  const masked = +samples.find(d => d.sample === 'holdout' && d.brand === 'Unknown').n;
  const known = samples.filter(d => d.sample === 'holdout' && d.brand !== 'Unknown').reduce((n, d) => n + +d.n, 0);
  assert.equal(masked + known, metadata.n_test);
  stat('ml.n', metadata.n_test, metadata.n_test, 'reports/ml/metadata.json', 'all-school holdout');
  stat('ml.masked', masked, masked, 'reports/ml/sample_counts.csv', 'all-school holdout');
  stat('ml.known', known, known, 'reports/ml/sample_counts.csv', 'all-school holdout');
  stat('ml.testSeasons', metadata.test_seasons, metadata.test_seasons.join(' and '), 'reports/ml/metadata.json', 'held-out seasons');
  const cases = [...new Set(events.filter(d => truth(d.usable_sensitivity)).map(d => d.school))].sort().map((school, i) => {
    const rows = events.filter(d => d.school === school && truth(d.usable_sensitivity)).sort((a, b) => +a.relative_season - +b.relative_season);
    const context = confounders.find(d => d.school === school);
    assert.ok(context);
    const points = rows.map((d, j) => {
      const value = d.points_pctile === '' ? null : +d.points_pctile;
      assert.equal(truth(d.outcome_available), value !== null);
      stat(`case.${i}.${j}.relative`, +d.relative_season, +d.relative_season > 0 ? `+${d.relative_season}` : d.relative_season, 'exports/tableau/switch_events.csv', 'usable_sensitivity=True; gaps retained');
      stat(`case.${i}.${j}.season`, d.season, d.season, 'exports/tableau/switch_events.csv', 'case calendar season');
      stat(`case.${i}.${j}.value`, value, value === null ? 'No annual final / not available' : format(value, 2), 'exports/tableau/switch_events.csv', 'A+B observed outcomes; missing slots retained');
      return { relative: +d.relative_season, season: d.season, value, brand: d.observed_brand || null };
    });
    const note = [truth(context.covid_gap) ? context.covid_note : '', context.realignment_note, context.coaching_change].filter(Boolean).join(' ');
    stat(`case.${i}.note`, note, note, 'reports/switch_case_confounders.csv', 'descriptive context; targeted screen');
    stat(`case.${i}.season`, rows[0].switch_season, rows[0].switch_season, 'exports/tableau/switch_events.csv', 'switch season');
    const shortNote = [truth(context.covid_gap) ? 'COVID gap' : '', truth(context.observed_realignment) ? context.observed_conferences + ' realignment' : '', context.coaching_status === 'identified' ? 'coaching change identified' : 'coaching stability not established'].filter(Boolean).join(' · ');
    stat(`case.${i}.shortNote`, shortNote, shortNote, 'reports/switch_case_confounders.csv', 'targeted confounder screen');
    return { school, shortNote, from: rows[0].from_brand, to: rows[0].to_brand, switchSeason: rows[0].switch_season, transitionDate: rows[0].transition_date, points, note, coachingSource: context.coaching_source_url, realignmentSource: context.realignment_source_url, covid: truth(context.covid_gap) };
  });
  const excluded = [...new Set(events.filter(d => !truth(d.usable_sensitivity)).map(d => d.school))];
  stat('cases.n', cases.length, cases.length, 'exports/tableau/switch_events.csv', 'usable_sensitivity=True');
  stat('cases.documented', validation.documented_switch_events, validation.documented_switch_events, 'reports/database_validation.json', 'documented transitions');
  stat('cases.cancelledSeason', '2019-20', '2019–20', 'docs/methodology.md', 'COVID cancelled annual final');
  stat('cases.reference', 0, '0', 'exports/tableau/switch_events.csv', 'relative season zero = switch season');
  const coverageRate = 100 * validation.covered_priority_school_seasons / validation.priority_school_seasons;
  assert.ok(Math.abs(coverageRate - validation.coverage_percent) < .005);
  stat('coverage.rate', coverageRate, `${format(coverageRate, 1)}%`, 'reports/database_validation.json', 'selected 74-school research scope; A+B+C');
  for (const [key, raw] of Object.entries({ schools: validation.priority_schools, covered: validation.covered_priority_school_seasons, total: validation.priority_school_seasons, unknown: validation.unknown_priority_school_seasons })) stat(`coverage.${key}`, raw, raw, 'reports/database_validation.json', 'selected research scope');
  for (const tier of ['A', 'B', 'C']) stat(`coverage.${tier}`, validation.evidence_tier_counts[tier], validation.evidence_tier_counts[tier], 'reports/database_validation.json', 'selected research scope');
  const seasons = new Set(panel.map(d => d.season)).size;
  stat('seasons', seasons, seasons, 'exports/tableau/school_season.csv', 'distinct competition seasons');
  const findingLines = readme.split('\n').filter(d => d.startsWith('- **'));
  const brandCopy = plain(findingLines.find(d => d.includes('The best programs wear Nike'))).replace(/ Source\.$/, '');
  const pickCopy = plain(findingLines.find(d => d.includes('Pick or make'))).replace(/ Mean gaps and model comparison\.$/, '');
  const mlCopy = plain(findingLines.find(d => d.includes('Predicting next season'))).split(' Results, including RMSE improvements')[0].trim();
  brands.forEach((d, i) => assert.ok(brandCopy.includes(`${registry[`brand.${i}.rate`].text} for ${d.brand} (${d.finishes}/${d.n}`), 'README brand number mismatch'));
  comparisons.forEach(d => assert.ok(pickCopy.includes(format(d.meanGap, 2)), 'README raw lead mismatch'));
  assert.ok(pickCopy.includes(shrinkRange), 'README attenuation mismatch');
  assert.ok(mlCopy.includes(`${metadata.n_test} held-out school-seasons`) && mlCopy.includes(`of ${featureRows.length} features`) && mlCopy.includes('on mean absolute error'));
  models.forEach(d => assert.ok(mlCopy.includes(format(d.mae, 2)), 'README MAE mismatch'));
  assert.ok(readme.includes(`${seasons} seasons of NCAA Directors' Cup data`));
  for (const entry of ledger.filter(d => d.kind === 'finding')) {
    assert.equal(entry.status, 'PASS');
    assert.ok(readme.includes(entry.displayed_value), `README ledger value missing: ${entry.displayed_value}`);
  }
  const copy = {
    hero: "I ONLY WANTED TO ROW FOR A NIKE SCHOOL.",
    subhead: `So I tested whether Nike schools actually win more. The Swoosh Effect: ${seasons} seasons of NCAA Directors' Cup data.`,
    brand: brandCopy, pick: pickCopy, ml: mlCopy,
    why: plain(readme.split('## Why I built this')[1].split('## Key findings')[0]),
  };
  for (const [key, text] of Object.entries(copy)) stat(`copy.${key}`, text, text, 'README.md', 'README wording; generated numbers');
  const links = {
    github: 'https://github.com/alexandrajcowan275/swoosh-effect',
    tableau: readme.match(/\[Tableau dashboard\]\(([^)]+)\)/)[1],
    linkedin: readme.match(/\[Alexandra Cowan\]\(([^)]+)\)/)[1],
    methodology: 'https://github.com/alexandrajcowan275/swoosh-effect/blob/main/docs/methodology.md',
    sources: 'https://github.com/alexandrajcowan275/swoosh-effect/blob/main/docs/data_sources.md',
    quote: 'https://about.nike.com/en/mission',
    attribution: 'https://media.corporate-ir.net/media_files/irol/10/100529/Areports/ar_07/pdfs/Nike_AR_MParker_2007.pdf',
  };
  const story = { sample: headlineSample, seasons, brands, comparisons, ml: { models, features, featureCount: featureRows.length, n: metadata.n_test, masked, known, testSeasons: metadata.test_seasons }, cases, excluded, coverage: validation, copy, links, registry };
  return { story, provenance: { tolerance, rounding: 'Rates one decimal; estimates/CI two decimals; importance three decimals; attenuation range whole percent. Counts exact.', sources: Object.fromEntries(Object.entries(sources).sort(([a], [b]) => a.localeCompare(b))) }, charts: generateCharts(story) };
}

async function main() {
  const files = await generateData();
  await mkdir(resolve(siteRoot, 'data'), { recursive: true });
  for (const [name, data] of Object.entries(files)) {
    const expected = JSON.stringify(data, null, 2) + '\n';
    const path = resolve(siteRoot, 'data', `${name}.json`);
    if (process.argv.includes('--check')) assert.equal(await readFile(path, 'utf8'), expected, `Stale ${name}.json; run npm run build-data`);
    else await writeFile(path, expected);
  }
  console.log(`PASS: source reconciliation, README number ledger, ${Object.keys(files.story.registry).length} display values, ${files.story.cases.length} switch cases.`);
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
