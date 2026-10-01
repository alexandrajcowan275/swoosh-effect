import test from 'node:test';
import assert from 'node:assert/strict';
const luminance = hex => {
  const c = hex.replace('#', '').match(/../g).map(n => parseInt(n, 16) / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
};
const ratio = (a, b) => (Math.max(luminance(a), luminance(b)) + .05) / (Math.min(luminance(a), luminance(b)) + .05);
test('every declared text/background pair meets WCAG AA normal-text contrast', () => {
  const pairs = [['#FFFFFF', '#000000'], ['#E9533A', '#000000'], ['#B8B8B8', '#000000'], ['#DDDDDD', '#000000'], ['#D3D3D3', '#000000'], ['#000000', '#FFFFFF'], ['#555555', '#FFFFFF'], ['#000000', '#F3F5F4'], ['#000000', '#E9533A']];
  for (const [text, background] of pairs) assert.ok(ratio(text, background) >= 4.5, `${text} on ${background} = ${ratio(text, background)}`);
});
