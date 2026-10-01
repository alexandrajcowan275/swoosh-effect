import { spawn } from 'node:child_process';
import { mkdir, readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
await mkdir('.lighthouse', { recursive: true });
for (const mode of ['mobile', 'desktop']) {
  const args = ['http://localhost:3000', '--quiet', '--chrome-flags=--headless --disable-gpu --no-first-run', '--only-categories=performance,accessibility', '--output=json', `--output-path=.lighthouse/${mode}.json`];
  if (mode === 'desktop') args.push('--preset=desktop');
  await new Promise((resolve, reject) => {
    const process = spawn('./node_modules/.bin/lighthouse', args, { stdio: 'inherit' });
    process.on('exit', code => code === 0 ? resolve() : reject(new Error(`Lighthouse exit ${code}`)));
  });
  const report = JSON.parse(await readFile(`.lighthouse/${mode}.json`, 'utf8'));
  const scores = Object.fromEntries(Object.entries(report.categories).map(([key, value]) => [key, Math.round(value.score * 100)]));
  console.log(`${mode}: ${JSON.stringify(scores)}`);
  for (const [key, score] of Object.entries(scores)) assert.ok(score >= 90, `${mode} ${key}: ${score} < 90`);
}
