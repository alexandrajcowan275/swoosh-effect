# Swoosh Effect data story

A static Next.js story built from the audited project outputs. No backend, API keys, analytics or external font requests.

From this directory, with the Node version in `.nvmrc`:

```bash
npm ci
npm run build
npm run preview
```

Open `http://localhost:3000`. `npm run dev` is available for editing after `npm run build-data`.

`npm run build-data` reads the parent repository’s reports and Tableau exports, reconciles the A+B headline sample against `README.md` and its existing number ledger, then generates:

- `data/story.json`: values, exact README finding text, source references and a display registry.
- `data/provenance.json`: input hashes, rounding rules and numerical tolerance.
- `data/charts.json`: static Observable Plot SVGs, generated from those same values.

`npm run check-data` rejects stale JSON. The production build verifies all rendered numbers and chart marks against freshly computed data. Numeric text without a registered source or an explicit definition is rejected. Mutation tests prove that wrong README values, rendered statistics and chart marks fail. Existing scientific outputs are never modified.

`npm run audit-ui` measures mobile and desktop Lighthouse performance/accessibility against the running static preview and rejects a score below 90; Chrome must be installed. Reports are saved locally in the ignored `.lighthouse/` folder.

`npm test` and `npm run typecheck` cover source reconciliation, cancelled-season gaps, regression sample labels, numeric mutations and contrast. The authorized GitHub Actions site job installs locked packages and runs those checks without downloading Directors’ Cup PDFs.

Charts render during the build rather than shipping a charting library to the browser. Native disclosure controls expose chart values and confounder sources. All content is available without JavaScript; the only client component adds optional scroll-in motion and respects reduced-motion preferences.

## Personal material

The hero is a plain black background with the headline. Section “Why Nike” uses Alexandra’s original USC commitment graphic, preserved unedited and uncropped in `public/images/usc-commit.jpg`. `npm run build-images` creates responsive WebP/AVIF derivatives with width-only resizing; tests verify their dimensions, aspect ratio and the original file hash. The portrait is beside the story on desktop and above it on mobile, with a descriptive alt text and caption.

The author’s exact personal paragraph, caption and alt text live in `content/personal.json`. The rendered build checks them against that source. The bar-chart favicon is an original graphic; no brand logo was created for the site.

## Share preview

`public/share.png` is generated from the verified headline with the free Barlow Condensed font. Font licensing is in `public/fonts/OFL-Barlow-Condensed.txt`; Google Font web files are supplied by pinned Fontsource packages. Inter is used for body text.

The static export is `out/`. Share metadata derives its absolute host from Vercel’s `VERCEL_PROJECT_PRODUCTION_URL` or `VERCEL_URL` system variables at build time, with localhost used for local previews. No environment secrets are required. A production URL and root README link will be added once the site is live.

## Interpretation

The raw average percentile gaps and matched regression coefficients are different quantities and remain labeled separately. Major-brand confidence intervals include zero. The forecasting statement applies to MAE; RMSE improvements remain visible. Brand masking prevents a general conclusion of zero brand effect. Switch charts preserve missing calendar seasons and are descriptive case studies.

Independent student project by Alexandra Cowan. Not affiliated with or endorsed by Nike, Inc.

## Vercel import

Import this GitHub repository as a Next.js project with Root Directory `site`. Enable **Include source files outside of the Root Directory in the Build Step**, because the data build reads the parent repository’s audited reports and CSVs. Use Node.js 24.x, install command `npm ci --include=dev`, build command `npm run build`, and output directory `out`. No environment secrets are required. Deployment steps: <https://vercel.com/docs/monorepos/monorepo-faq>.
