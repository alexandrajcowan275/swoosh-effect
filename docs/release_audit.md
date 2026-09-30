# Publication audit — September 30, 2026

The five release fixes are complete. The public history uses the GitHub noreply identity for every author and committer. The README, dashboard guide and published Tableau headline read “The best programs wear Nike,” followed immediately by the descriptive selection/persistence caveat. No site directory or site-copy files are present in this repository.

| Check | Result | Verification |
|---|---|---|
| macOS Bash compatibility | PASS | Real default pipeline under `/bin/bash` 3.2.57; default, forced-download and offline routing covered by tests. No Bash 4+ features in run.sh. |
| Fresh-clone reproducibility | PASS | All 24 recorded PDFs downloaded and SHA-256 verified; complete pipeline and 112 tests passed. Pinned Python 3.12.14 dependencies were installed into an isolated environment. A temporary OpenMP runtime supplied the documented Mac prerequisite; no system installation was performed. |
| Standalone test suite | PASS | Fresh-clone pytest: 112 passed. |
| Docker | PASS | Pristine checkout build succeeds; non-root, network-disabled container rebuilds the offline pipeline and passes 112 tests. |
| CI | PASS | [GitHub Actions run 36785885506](https://github.com/alexandrajcowan275/swoosh-effect/actions/runs/36785885506): full tests, pre-commit checks and complete-history secret scan all pass after the privacy rewrite. |
| Numbers | PASS | Counts/assignments agree exactly; numeric outputs agree within absolute 1e-9 and zero relative tolerance. Published finish rates and model/sample labels reconcile; no stale headline statistic or inconsistent rounding was found. See the README's numerical reproducibility rule and [Tableau expected values](tableau_expected_values.md). |
| Security and privacy | PASS | Zero Gitleaks findings in working tree and rewritten GitHub history; zero tokenized URLs across all commits. Fresh-clone author and committer email sets contain only the ID-based noreply address. No personal absolute paths remain in current tracked files. |
| Links | PASS | All 47 README link occurrences resolve. The interactive Tableau dashboard loads and shows the updated text. |
| Claims and graphics | PASS | Descriptive selection/persistence interpretation; no causal or general zero-brand-effect claims. ML masking caveat remains explicit. Screenshot contains the dashboard itself, without Tableau's surrounding header/toolbar branding. No Nike logos; disclaimer remains present. |
| Cleanup | PASS | Stale publication/phase text fixed in generators and generated reports; Vercel placeholder removed; six unused imports removed. No TODO/FIXME/debug breakpoints; notebook has no error outputs or oversized outputs. Raw third-party pages, PDFs, search logs, caches, environments and DuckDB are not tracked. |

The code audit ran on `01d4f68` after rewriting history; the following publication commit adds only this record and the refreshed dashboard screenshot. Historical runs in [engineering validation](engineering_validation.md) retain their original dates and test counts. Their earlier commit identifiers describe the pre-rewrite history.

Research limitations are unchanged: 55 priority school-seasons remain unknown, 70 use inferred Tier C, and the selected cohort is not a D1 census. ML brand importance is limited by 661 masked holdout rows. Source revisions and sport-level discrepancies remain documented. These are disclosed study limitations, not failed release checks.

Independent student project. Not affiliated with or endorsed by Nike, Inc.
