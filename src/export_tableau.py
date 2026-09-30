"""Export the audited analysis without changing values or hiding missingness."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def export_tableau(root=ROOT):
    root=Path(root)
    panel=pd.read_csv(root/'data/processed/analysis_panel.csv')
    summary=pd.read_csv(root/'reports/brand_summary.csv')
    events=pd.read_csv(root/'reports/switch_case_observations.csv')
    folder=root/'exports/tableau';folder.mkdir(parents=True,exist_ok=True)
    school=panel[['school','season','conference_model','brand','evidence_tier','rank','total_points','panel_points_pctile',
        'in_research_scope','zero_imputed','conference_basis','sponsor_source_url']].rename(
        columns={'conference_model':'conference','panel_points_pctile':'points_pctile'})
    school['rank']=school['rank'].astype('Int64')
    school['primary_included']=school.in_research_scope & school.evidence_tier.isin(['A','B','C'])
    school['sensitivity_included']=school.in_research_scope & school.evidence_tier.isin(['A','B'])
    school.loc[school.conference.isna(),'conference_basis']='not available; imputed zero year'
    school=school.sort_values(['school','season']).reset_index(drop=True)
    summary=summary.rename(columns={'mean_percentile':'mean_points_pctile','median_percentile':'median_points_pctile'})
    summary=summary.sort_values(['evidence_tiers','brand']).reset_index(drop=True)
    switches=events[['school','from_brand','to_brand','switch_season','relative_season','points_pctile',
        'season','evidence_tier','brand','outcome_available','primary_included','sensitivity_included',
        'usable_primary','usable_sensitivity','transition_date','transition_date_precision']].rename(columns={'brand':'observed_brand'})
    switches=switches.sort_values(['school','switch_season','relative_season']).reset_index(drop=True)
    assert not school.duplicated(['school','season']).any()
    assert not summary.duplicated(['evidence_tiers','brand']).any()
    assert not switches.duplicated(['school','switch_season','relative_season']).any()
    assert school.loc[school.evidence_tier.eq('unknown'),'brand'].isna().all()
    assert school.loc[school.zero_imputed,'rank'].isna().all()
    assert school.loc[school.zero_imputed,'total_points'].eq(0).all()
    assert switches.points_pctile.isna().equals(~switches.outcome_available)
    for name,frame in [('school_season',school),('brand_summary',summary),('switch_events',switches)]:
        frame.to_csv(folder/f'{name}.csv',index=False,na_rep='')
    counts=dict(school_season_rows=len(school),schools=school.school.nunique(),brand_summary_rows=len(summary),
        switch_event_rows=len(switches),switches=switches[['school','switch_season']].drop_duplicates().shape[0],
        unknown_provider_rows=int(school.brand.isna().sum()),retained_zero_rows=int(school.zero_imputed.sum()),
        missing_switch_outcomes=int(switches.points_pctile.isna().sum()),primary_rows=int(school.primary_included.sum()),
        sensitivity_rows=int(school.sensitivity_included.sum()),missing_conferences=int(school.conference.isna().sum()))
    (folder/'README.md').write_text(dictionary(counts))
    (root/'reports/tableau_export_validation.json').write_text(json.dumps(counts,indent=2)+'\n')
    print(json.dumps(counts,indent=2))
    return counts


def dictionary(c):
    return f'''# Tableau handoff: The Swoosh Effect

Three UTF-8 CSVs, in tidy long format. Files are local; nothing has been published
to Tableau Public. Rebuild from the project directory:

```bash
python -m src.export_tableau
```

Run `python src/build_database.py` and `python -m src.analyze` first if inputs
changed. `run.sh` rebuilds the complete pipeline, exports, and tests.

| File | Grain / key | Rows |
|---|---|---:|
| [school_season.csv](school_season.csv) | One institution per academic season; school + season | {c['school_season_rows']:,} |
| [brand_summary.csv](brand_summary.csv) | One brand per evidence version; evidence_tiers + brand | {c['brand_summary_rows']} |
| [switch_events.csv](switch_events.csv) | One event per relative calendar season; school + switch_season + relative_season | {c['switch_event_rows']} |

The school panel has {c['schools']} institutions appearing at least once in the
input final standings. It is **not a census of all Division I members**. The
sponsorship research scope is 74 schools / 592 seasons: 537 covered (90.7%),
including A=445, B=22, C=70; 55 unknown. Across the full exported panel,
537/{c['school_season_rows']:,} rows have provider assignments; the other
{c['unknown_provider_rows']:,} are blank, mostly outside the research scope.
Do not describe 90.7% as coverage of the entire D1 panel.

## Recommended Tableau setup

1. Connect `school_season.csv` as a text data source. Treat `season` as text,
   `school`, `brand`, `evidence_tier` and `conference` as dimensions, flags as
   booleans, and numeric columns as measures. Sort seasons by the first four digits.
2. For the primary comparison, filter `primary_included = True` (A+B+C, n=537).
   For sensitivity, use `sensitivity_included = True` (A+B, n=467). Never convert
   a blank brand to `other`: that label is reserved for known smaller providers.
3. Use **AVG** or **MEDIAN** of `points_pctile`, not SUM. Rank is not additive.
   Count rows for school-seasons; use COUNTD(school) for institutions. A switching
   school can contribute to more than one brand, so per-brand unique-school
   counts are not additive.
4. Keep `brand_summary.csv` as a separate data source or aggregate logical table.
   **Filter exactly one `evidence_tiers` value before aggregation.** The two
   samples overlap and must not be summed. Do not physically join its totals
   onto every school-season row, and do not average its precomputed medians.
5. For switch charts, use `switch_events.csv`, one school per chart, with
   `relative_season` on the x-axis and `points_pctile` on the y-axis. Keep null
   slots visible; do not connect a line across the cancelled 2019-20 season.
   Use the inclusion/usability flags for comparisons. t=0 is the first post
   season: the −2 through +2 window allows two pre and three post seasons.
   These are descriptive case studies, not causal effects.

## school_season.csv

The first eight columns are the requested analysis fields; the remaining
columns retain essential audit and filtering information. Blank CSV values are
NULL/unknown, not zero. Booleans are written as `True`/`False`.

| Column | Type | Meaning / missingness |
|---|---|---|
| school | Text | Canonical institution name from the reviewed name map. |
| season | Text | Academic season `YYYY-YY`; eight seasons 2017-18 through 2025-26, excluding 2019-20. |
| conference | Text, nullable | Season-specific conference used in analysis. Pac 12 spelling normalized to Pac-12; the Harvard and Yale zero-year classifications use agreeing neighboring Ivy League records. Other {c['missing_conferences']} missing conferences remain blank. |
| brand | Text, nullable | Department primary provider: Nike (includes Jordan), adidas, Under Armour, or other. Unknowns stay blank. Team exceptions are not modeled. |
| evidence_tier | Text | A, B, C, or unknown. A includes labeled reported contract terms; B is dated official use; C is bounded continuity inference. |
| rank | Integer, nullable | Official final Directors' Cup rank. All retained zero rows have blank rank, never rank 0. |
| total_points | Decimal | Official department total. The {c['retained_zero_rows']} reviewed D1 zero rows contain 0; they may reflect cancellations or postseason restrictions. |
| points_pctile | Decimal, 0–100 | Audited within-season panel percentile, defined below. This is not the older published-scoring-schools-only percentile. |
| in_research_scope | Boolean | True for the 74-school sponsor research cohort: current Power 4 plus other ever-top-50 schools. |
| zero_imputed | Boolean | True for an absent final-standings row kept after the D1 program eligibility review. |
| conference_basis | Text | Printed/normalized conference, documented neighboring-season inference, or unavailable. |
| sponsor_source_url | Text, nullable | Direct evidence URL; for C, the left anchor URL. Both anchors and all provenance are in the season evidence audit linked below. |
| primary_included | Boolean | Research-scope row with tier A, B, or C. |
| sensitivity_included | Boolean | Research-scope row with tier A or B. |

`points_pctile = 100 × average ascending rank(total_points) / eligible panel
schools that season`. Ties receive their average rank. A zero may therefore have
a percentile above zero. The denominator includes reviewed eligible zeros but
excludes 31 pre-entry or post-departure/closure rows. Original annual totals are
not reconstructed from sport cells. Differences in sport offerings, resources
and Cup rules remain limitations.

## brand_summary.csv

Only covered research-cohort observations enter these summaries. Both evidence
versions are supplied; use one at a time. n means school-seasons, not athletes.

| Column | Type | Meaning |
|---|---|---|
| evidence_tiers | Text | `A+B+C` primary or `A+B` sensitivity. |
| brand | Text | Known provider category. |
| n_school_seasons | Integer | Number of rows in this brand/version group. |
| n_schools | Integer | Distinct institutions within the group; not additive across switching brands. |
| mean_points / median_points | Decimal | Mean/median annual official points; supplementary because totals vary across seasons. |
| mean_points_pctile / median_points_pctile | Decimal | Mean/median audited panel percentile in the group. |
| top10_finishes / top25_finishes | Integer | Counts with published rank ≤10 / ≤25. These columns are counts, not national market shares. |
| n_tier_A / n_tier_B / n_tier_C | Integer | Evidence-tier composition; sum equals n_school_seasons. C is zero in A+B. |

Do not infer national top-finish shares by dividing these counts only by known
brands: unknown-brand finishes must stay in the denominator. Complete share
denominators, including unassigned providers, are in
[brand_shares.csv](../../reports/brand_shares.csv).

## switch_events.csv

All {c['switches']} documented transitions are retained, with five calendar slots
each. There are {c['missing_switch_outcomes']} missing outcomes: cancelled or
outside the observation window. They remain blank. Nine events have at least
one covered pre and one covered post season under both evidence versions.
Denver has known pre-switch performance but unknown pre-switch providers within
the window, so it is not a supported before/after brand comparison.

| Column | Type | Meaning / missingness |
|---|---|---|
| school | Text | Switching institution. |
| from_brand / to_brand | Text | Documented event metadata. from_brand is **not** proof of the provider in every prior row. |
| switch_season | Text | First full season assigned to the new department provider. |
| relative_season | Integer | Actual calendar-year offset, −2 through +2. Missing seasons do not compress time. |
| points_pctile | Decimal, nullable | Same audited percentile as school_season; missing means unavailable, never zero. |
| season | Text | Actual calendar-aligned academic season, including missing slots. |
| evidence_tier | Text | Season-level A/B/C/unknown, not the tier of the event announcement. |
| observed_brand | Text, nullable | Provider assigned for this particular season; blank when unknown. C, if present, is inferred despite this column name. |
| outcome_available | Boolean | A sourced or reviewed-zero outcome exists for this calendar slot. |
| primary_included / sensitivity_included | Boolean | Outcome and qualifying tier exist, and assigned brand matches the documented pre/post provider. |
| usable_primary / usable_sensitivity | Boolean | This event has at least one included pre and post observation under that evidence rule. Repeated on its five rows. |
| transition_date | Text date | Recorded transition-related date; interpret with date precision. |
| transition_date_precision | Text | Effective date or announcement-date limitation. Denver's exact first competition use is not established. |

Washington remains t=0 in cancelled 2019-20; 2020-21 is t=+1, not a re-dated
switch. Count events with COUNTD(school + switch_season), not the 50-row count.
Coaching changes, COVID disruptions and realignment are documented in the
[case-study report](../../reports/switch_case_studies.html) and
[confounder table](../../reports/switch_case_confounders.csv).

## Sources and interpretation

- [Analysis report](../../reports/phase3_analysis.html): plain, matched-row and lagged models, school-clustered 95% intervals and limitations.
- [Research audit](../../reports/sponsor_research.html) and [season evidence](../../reports/sponsor_coverage.csv): source types, archive dates and both C anchors.
- [Zero-row audit](../../reports/zero_row_audit.csv): 469 reviewed, 438 kept, 31 dropped.
- [Model sample sizes](../../reports/model_sample_sizes.csv): n per brand and tier for each specification.

The apparent major-brand gaps shrink after controlling for prior performance;
this is consistent with persistence/selection, not proof of a causal “pick” or
“make” mechanism. Provider assignments do not establish payment continuity.
Unknown seasons, team exceptions, the selective sponsor scope, unmeasured
department resources, and the very small other-provider group remain limits.
No revenue adjustment was performed. These exports contain no regression
coefficients; use the linked analysis outputs for those results.
'''


if __name__=='__main__':
    export_tableau()
