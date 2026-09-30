# Data sources, provenance and outputs

The project studies all-sport athletic-department results, with rowing retained as an optional supporting cut. [Methodology](methodology.md) defines the study cohorts, evidence rules, percentiles, models and limitations.

## Source registry and published outputs

- **Directors' Cup standings:** [NACDA's standings archive](https://nacda.com/sports/2018/7/17/directorscup-nacda-directorscup-previous-standings-html.aspx). The [eight final-source records](../data/sources.json) and [sixteen fall/winter records](../data/seasonal_sources.json) retain canonical PDF URLs, landing URLs, retrieval dates, filenames, and SHA-256 hashes. PDFs are downloaded locally rather than redistributed in this repository.
- **Provider evidence:** official athletics announcements, board records, contract documents, dated guides, and labeled secondary reporting in [sponsor_evidence.json](../data/sponsor_evidence.json). Archived official-page evidence links to the [Internet Archive's Wayback Machine](https://web.archive.org/), with snapshot dates retained in the evidence tables. The [research report](../reports/sponsor_research.html) explains decisions and unresolved gaps.
- **Transition context:** official athletics releases cited in [switch_confounders.json](../data/switch_confounders.json) and the [confounder table](../reports/switch_case_confounders.csv).
- **Analysis-ready exports:** [school_season.csv](../exports/tableau/school_season.csv), [brand_summary.csv](../exports/tableau/brand_summary.csv), and [switch_events.csv](../exports/tableau/switch_events.csv), with a [data dictionary](../exports/tableau/README.md). Unknown providers remain visible in the full export.
- **Rebuildable analysis:** [Python pipeline](../src/), [SQL summaries](../sql/descriptive_summaries.sql), [analysis notebook](../notebooks/analysis.ipynb), and [validation outputs](../reports/). An additional Jupyter/IPython environment is only needed to execute the notebook interactively.

## PDF downloads and source integrity

The frozen manifests describe 24 Directors' Cup PDFs: eight annual final standings and sixteen fall/winter standings. Each record preserves its source and landing URLs, retrieval date, local filename and SHA-256 checksum. See [all PDF URLs and manual recovery instructions](DATA_DOWNLOADS.md).

`./run.sh` downloads missing or invalid files and requires the recorded hashes. `./run.sh --download` refreshes the PDFs without accepting changed source bytes. The offline mode uses committed audited tables instead. A changed checksum stops the rebuild and requires a source review; replacing a hash just to bypass validation is not supported.

Annual final standings remain authoritative for department totals. Sport-level tables retain documented revisions and discrepancies, so summing the combined sport observations is not a replacement for annual totals. [Source discrepancies](../reports/source_discrepancies.csv) and [period reconciliation](../reports/period_reconciliation.csv) document the differences. The modeled percentile is recomputed within the audited eligible observed-ever panel; original scoring-school-only source percentiles remain available separately.

## Provider and membership provenance

The [season evidence table](../data/processed/sponsor_seasons.csv) retains source URLs, archive snapshot URLs, dates, source types and inference anchors. Accepted secondary reporting of contract terms is labeled. The [research report](../reports/sponsor_research.html) and [coverage table](../reports/sponsor_coverage.csv) explain decisions and unresolved gaps.

The [membership review](../data/division_i_membership_review.csv) and [zero-row audit](../reports/zero_row_audit.csv) distinguish retained D1 zero-point observations from invalid seasons. Transition context is traceable through the [confounder register](../data/switch_confounders.json) and [case table](../reports/switch_case_confounders.csv). Team exceptions and payment disputes are documented; neither creates a separately modeled team assignment.

Source URLs are canonical and do not retain signed or tokenized query parameters. The repository does not republish third-party webpages, raw search logs or source PDFs. Downloaded PDFs, DuckDB, caches and virtual environments are ignored by Git. No API key is needed to rebuild.

## Tableau dashboard and chart provenance

[Explore the published Tableau Public dashboard](https://public.tableau.com/views/TheSwooshEffect/TheSwooshEffect) for top-10 finish rates, performance trends by brand, and nine descriptive switch case studies. The dashboard uses direct evidence (A+B).

[![Published Tableau dashboard showing top-10 finish rates and performance trends by brand](../docs/images/tableau-dashboard.jpg)](https://public.tableau.com/views/TheSwooshEffect/TheSwooshEffect)

The [Tableau dictionary](../exports/tableau/README.md), [build guide](tableau_build_guide.md) and [expected values](tableau_expected_values.md) explain data types, denominators, evidence filters and missing switch-season slots. [README headline provenance](readme_number_ledger.csv) connects the concise summary to its machine-readable outputs.

## Code and third-party rights

Original project code is released under the [MIT License](../LICENSE). Third-party source documents and data retain their respective owners' rights; source links and attribution are provided above. Downloaded source PDFs and archived third-party webpages are not included in Git.

Independent student project. Not affiliated with or endorsed by Nike, Inc.
