import * as Plot from '@observablehq/plot';
import { JSDOM } from 'jsdom';

export function generateCharts(story) {
  const document = new JSDOM('').window.document;
  let sequence = 0;
  const plot = (id, options) => {
    const svg = Plot.plot({ document, width: 680, style: { background: 'transparent', color: 'currentColor', fontFamily: 'Inter, sans-serif', fontSize: '14px' }, ...options });
    // Observable generates process-global IDs; normalize for byte-for-byte checks.
    const ids = new Map();
    let result = svg.outerHTML.replace(/id="([^"]+)"/g, (_, old) => { const next = `${id}-clip-${sequence++}`; ids.set(old, next); return `id="${next}"`; });
    for (const [old, next] of ids) result = result.replaceAll(`url(#${old})`, `url(#${next})`);
    result = result.replace(/class="plot-[^"]+"/, 'class="observable-chart"').replace(/\.plot-[\w-]+/g, '.observable-chart');
    return result;
  };
  const charts = {};
  const store = (id, options) => {
    charts[id] = plot(id, options);
    const mobile = { ...options, width: 400, style: { background: 'transparent', color: 'currentColor', fontFamily: 'Inter, sans-serif', fontSize: '14px' } };
    if (id === 'rates') { mobile.marginLeft = 106; mobile.marginRight = 48; mobile.x = { ...options.x, ticks: [0, 10, 20], label: 'Within-brand top-10 rate →' }; }
    if (id.startsWith('comparison')) { mobile.marginLeft = 128; mobile.x = { ...options.x, ticks: [-2, 0, 4, 8], label: 'Nike advantage, points →' }; }
    if (id === 'importance') { mobile.marginLeft = 166; mobile.height = 450; mobile.x = { ...options.x, ticks: [0, .1, 1, 10] }; mobile.y = { ...options.y, tickFormat: d => d.replace('outdoor track and field', 'outdoor track').replace('swimming and diving', 'swimming').replace('Last season’s percentile', 'Last season').replace('indoor track and field', 'indoor track') }; }
    if (id.startsWith('case-')) { mobile.width = 320; mobile.height = 180; mobile.style.fontSize = '13px'; }
    charts[`${id}-mobile`] = plot(`${id}-mobile`, mobile);
  };
  store('rates', { height: 250, marginLeft: 118, marginRight: 65, marginBottom: 46, x: { label: 'Top-10 finish rate within brand →', domain: [0, 25], ticks: [0, 5, 10, 15, 20, 25], tickFormat: d => `${d}%`, grid: true }, y: { label: null, domain: story.brands.map(d => d.brand) }, marks: [Plot.barX(story.brands, { y: 'brand', x: 'rate', fill: 'color', insetTop: 14, insetBottom: 14 }), Plot.text(story.brands, { y: 'brand', x: 'rate', text: d => `${d.rate.toFixed(1)}%`, dx: 8, textAnchor: 'start', fontWeight: 600 })] });
  story.comparisons.forEach((d, i) => {
    store(`comparison-${i}`,  { height: 210, marginLeft: 126, marginRight: 22, marginBottom: 46, x: { domain: [-2, 8], label: 'Nike advantage, percentile points →', ticks: [-2, 0, 2, 4, 6, 8], grid: true }, y: { label: null, domain: d.estimates.map(e => e.label) }, marks: [Plot.ruleX([0], { stroke: '#888', strokeDasharray: '4,4' }), Plot.barX(d.estimates, { x: 'value', y: 'label', fill: 'color', insetTop: 17, insetBottom: 17 }), Plot.ruleY(d.estimates, { x1: 'low', x2: 'high', y: 'label', stroke: 'currentColor', strokeWidth: 1.5 }), Plot.tickX(d.estimates, { x: 'low', y: 'label', stroke: 'currentColor', length: 8 }), Plot.tickX(d.estimates, { x: 'high', y: 'label', stroke: 'currentColor', length: 8 }), Plot.dot(d.estimates, { x: 'value', y: 'label', fill: 'currentColor', r: 3 })] });
  });
  store('importance', { height: 430, marginLeft: 224, marginRight: 25, marginBottom: 48, x: { type: 'symlog', constant: .01, tickFormat: d => String(d), domain: [0, 20], ticks: [0, .01, .1, 1, 10], grid: true, label: 'MAE increase after shuffling →' }, y: { label: null, domain: story.ml.features.map(d => d.label) }, marks: [Plot.barX(story.ml.features, { x: 'importance', y: 'label', fill: d => d.rank === 1 ? '#E9533A' : '#767676', insetTop: 7, insetBottom: 7 })] });
  story.cases.forEach((d, i) => {
    store(`case-${i}`,  { width: 400, height: 190, marginLeft: 38, marginRight: 18, marginBottom: 45, x: { domain: [-2.15, 2.15], ticks: [-2, -1, 0, 1, 2], tickFormat: d => d > 0 ? `+${d}` : `${d}`, label: 'Seasons from switch →' }, y: { domain: [0, 100], ticks: [0, 50, 100], grid: true, label: 'Percentile ↑' }, marks: [Plot.ruleX([0], { stroke: '#777', strokeDasharray: '4,4' }), Plot.line(d.points, { x: 'relative', y: 'value', stroke: '#969696', strokeWidth: 2.5 }), Plot.line(d.points, { x: 'relative', y: e => e.brand === 'Nike' ? e.value : null, stroke: '#E9533A', strokeWidth: 2.5 }), Plot.dot(d.points, { x: 'relative', y: 'value', fill: e => e.brand === 'Nike' ? '#E9533A' : '#969696', r: 4 })] });
  });
  return charts;
}
