# Engineering validation

## CI — 2026-09-30

Commit `30f6e66` passed [GitHub Actions run 36746018965](https://github.com/alexandrajcowan275/swoosh-effect/actions/runs/36746018965).
Python 3.12.14 on Ubuntu 24.04 ran all 98 tests, pre-commit secret and URL checks,
and the complete Git-history Gitleaks scan. No research PDFs were downloaded.

## Docker — 2026-09-30

Built `swoosh-effect` locally on Apple Silicon using Docker CLI 29.8.1 and
Colima 0.10.3 (profile `swoosh`). The base is Python 3.12.14 slim Bookworm,
pinned by the multi-platform manifest digest in `Dockerfile`.

`docker --context colima-swoosh run --rm --network none swoosh-effect`
completed the offline pipeline and all **98 tests passed in 7.84 seconds**.
An independent `id -u` invocation returned **10001**. The run had no network,
no mounted host files, and no downloaded source PDFs. The application outputs
remain inside the disposable container; host research outputs are unchanged.

## ML and final container — 2026-09-30

Rebuilt the image after adding LightGBM 4.6.0 and scikit-learn 1.7.2. The same
non-root, network-disabled default container command rebuilt the full pipeline,
completed the benchmark, and passed **108 tests in 10.11 seconds**. The tests
include future-outcome perturbation, exact calendar lags, pre-season brand dates,
training-only preprocessing, whole-season splits, paired sample validation,
and reconciliation of reported metrics to individual held-out predictions.

The held-out sample is 712 school-seasons (2024-25 and 2025-26), from 356 schools.
There are 1,413 development rows and three expanding-origin validation years:
2021-22, 2022-23, and 2023-24. The benchmark uses 2,000 school-cluster bootstrap
resamples and 30 within-season permutations; see `reports/ml/metadata.json` for
input hashes, versions, the fixed seed, and selected parameters. No tuning used
held-out outcomes. The standalone benchmark and full offline rebuild produced
the same reported metrics. Regenerated CSV formatting differs at the byte level,
so the publication report is generated directly from the committed CSV bytes;
its input hashes are verified separately. Parsed rebuilt tables match the
committed values within a 1e-12 numerical tolerance.

Final publication-image test run: **109 passed in 10.02 seconds**, including the
additional input-hash provenance regression. All four recorded input hashes
match the committed research files.
