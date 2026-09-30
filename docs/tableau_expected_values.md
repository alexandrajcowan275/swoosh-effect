# Tableau expected values

Use these checks after connecting directly to the committed CSVs in [exports/tableau](../exports/tableau). All counts and fractions below are derived from the school-season and switch-event rows, then reconciled against all eight rows of [brand_summary.csv](../exports/tableau/brand_summary.csv). Counts and fractions are exact; displayed means and percentage rates are rounded to six decimal places. Small differences beyond those six places can reflect floating-point arithmetic.

Use `COUNT([school])` for **n school-seasons** on the brand charts. `COUNTD([school])` counts distinct institutions across the selected seasons and is not the rate denominator. A school can appear under different brands in different seasons, so distinct-school counts by brand do not add to the overall distinct-school count.

`points_pctile` already ranges from 0 to 100: use `AVG([points_pctile])` and a numeric format. Do not apply Tableau percentage formatting to that field. A finish-rate calculation ranges from 0 to 1 and can be formatted as a percentage.

## Check the filters first

Use one evidence sample at a time. `primary_included=True` uses A+B+C; `sensitivity_included=True` uses A+B. Setting both flags to True gives the narrower A+B sample.

| Filter state for school_season.csv | Rows / school-seasons | Distinct schools | NULL brand rows |
| --- | ---: | ---: | ---: |
| No filters | 2,833 | 358 | 2,296 |
| in_research_scope=True | 592 | 74 | 55 |
| in_research_scope=True, then primary_included=True | 537 | 73 | 0 |
| Same primary filter, then exclude NULL brand | 537 | 73 | 0 |
| in_research_scope=True, then sensitivity_included=True | 467 | 73 | 0 |
| Same sensitivity filter, then exclude NULL brand | 467 | 73 | 0 |

The 592-row research scope contains 445 Tier A, 22 Tier B, 70 Tier C, and 55 unknown rows. Both inclusion flags already imply research scope and a known brand. Applying their filters directly therefore gives the same 537 or 467 rows. Outside the research scope, the remaining 2,241 rows have no provider assignment. Those rows support the performance panel but are not part of the brand comparisons.

Blank CSV brands become NULL/unknown in Tableau; they are not the `other` brand category. `Other` is a known provider category with seven included school-seasons. Do not convert an unknown brand or missing outcome to zero.

The main school-season file has one row per eligible school-season and no 2019-20 season. Its 438 validated imputed zero-point rows are real retained observations; they are different from missing switch-event outcomes.

| season_order | Season | Unfiltered rows | Research scope | A+B+C rows | A+B rows |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 2017-18 | 348 | 74 | 68 | 68 |
| 2 | 2018-19 | 350 | 74 | 67 | 58 |
| 3 | 2020-21 | 354 | 74 | 68 | 58 |
| 4 | 2021-22 | 355 | 74 | 69 | 59 |
| 5 | 2022-23 | 358 | 74 | 69 | 57 |
| 6 | 2023-24 | 356 | 74 | 66 | 52 |
| 7 | 2024-25 | 356 | 74 | 65 | 50 |
| 8 | 2025-26 | 356 | 74 | 65 | 65 |

## Brand finish rates and overall means

A top-10 finish is a published non-NULL `rank <= 10`; a top-25 finish is a published non-NULL `rank <= 25`. Otherwise the corresponding finish indicator is zero. The denominator is every school-season in the selected brand and evidence sample, including valid imputed zero-point seasons. These are within-brand rates, not shares of national top-10 or top-25 places.

For each brand, use `SUM([top10]) / COUNT([school])` or equivalently `AVG([top10])`; use the analogous top-25 calculation. Do not use Tableau percent-of-total across brands. The four brand counts must sum to the selected sample size.

### A+B: sensitivity_included=True

| Brand | n school-seasons | Distinct schools | Top-10 fraction | Top-10 rate | Top-25 fraction | Top-25 rate | Mean points_pctile |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Nike | 289 | 53 | 61/289 | 21.107266% | 133/289 | 46.020761% | 90.359388 |
| Under Armour | 86 | 14 | 3/86 | 3.488372% | 22/86 | 25.581395% | 86.636956 |
| adidas | 85 | 13 | 2/85 | 2.352941% | 18/85 | 21.176471% | 87.692953 |
| Other | 7 | 3 | 0/7 | 0.000000% | 0/7 | 0.000000% | 75.972539 |

### A+B+C: primary_included=True

| Brand | n school-seasons | Distinct schools | Top-10 fraction | Top-10 rate | Top-25 fraction | Top-25 rate | Mean points_pctile |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Nike | 350 | 53 | 67/350 | 19.142857% | 147/350 | 42.000000% | 89.722271 |
| Under Armour | 86 | 14 | 3/86 | 3.488372% | 22/86 | 25.581395% | 86.636956 |
| adidas | 94 | 13 | 2/94 | 2.127660% | 21/94 | 22.340426% | 87.823003 |
| Other | 7 | 3 | 0/7 | 0.000000% | 0/7 | 0.000000% | 75.972539 |

## Mean percentile by season and brand

Each cell is `AVG(points_pctile) (n school-seasons)`, using the same evidence filter as its heading. NULL means there are no included rows for that brand and season; it must remain a gap, not a zero. Within one season, `COUNT(school)` and `COUNTD(school)` happen to agree because each school has one row, but use the consistent school-season count for labels and tooltips.

### A+B: sensitivity_included=True

| Season | Nike | Under Armour | adidas | Other |
| --- | ---: | ---: | ---: | ---: |
| 2017-18 | 89.518025 (n=44) | 87.511052 (n=13) | 87.413793 (n=10) | 65.517241 (n=1) |
| 2018-19 | 89.941176 (n=34) | 87.813187 (n=13) | 87.610390 (n=11) | NULL (n=0) |
| 2020-21 | 91.304732 (n=32) | 80.117340 (n=13) | 88.241525 (n=12) | 85.875706 (n=1) |
| 2021-22 | 91.021127 (n=36) | 87.797695 (n=11) | 88.194622 (n=11) | 69.577465 (n=1) |
| 2022-23 | 91.332801 (n=35) | 87.379380 (n=11) | 86.229050 (n=10) | 70.949721 (n=1) |
| 2023-24 | 89.538645 (n=33) | 88.951311 (n=9) | 87.390762 (n=9) | 81.179775 (n=1) |
| 2024-25 | 91.002175 (n=31) | 88.307584 (n=8) | 87.162921 (n=10) | 81.741573 (n=1) |
| 2025-26 | 89.683350 (n=44) | 87.008427 (n=8) | 88.881086 (n=12) | 76.966292 (n=1) |

### A+B+C: primary_included=True

| Season | Nike | Under Armour | adidas | Other |
| --- | ---: | ---: | ---: | ---: |
| 2017-18 | 89.518025 (n=44) | 87.511052 (n=13) | 87.413793 (n=10) | 65.517241 (n=1) |
| 2018-19 | 89.069767 (n=43) | 87.813187 (n=13) | 87.610390 (n=11) | NULL (n=0) |
| 2020-21 | 90.052462 (n=42) | 80.117340 (n=13) | 88.241525 (n=12) | 85.875706 (n=1) |
| 2021-22 | 89.849765 (n=45) | 87.797695 (n=11) | 87.417840 (n=12) | 69.577465 (n=1) |
| 2022-23 | 90.589696 (n=45) | 87.379380 (n=11) | 86.801676 (n=12) | 70.949721 (n=1) |
| 2023-24 | 88.872574 (n=44) | 88.951311 (n=9) | 88.085206 (n=12) | 81.179775 (n=1) |
| 2024-25 | 90.129344 (n=43) | 88.307584 (n=8) | 88.029386 (n=13) | 81.741573 (n=1) |
| 2025-26 | 89.683350 (n=44) | 87.008427 (n=8) | 88.881086 (n=12) | 76.966292 (n=1) |

## Switch case studies: keep the missing slots

Use [switch_events.csv](../exports/tableau/switch_events.csv) as a separate chart source. It contains 50 calendar slots for ten events. Filtering `usable_sensitivity=True` keeps **45 slots across nine schools: 35 non-NULL outcomes and ten NULL gaps**. All 35 observed points meet A+B and are Tier A; the A+B+C usable filter selects the same cases and points.

`usable_sensitivity` is an event-level eligibility flag: the case has at least one included pre-switch and one included post-switch observation. `sensitivity_included` is a row-level evidence flag. Filtering the latter to True would remove the ten gap rows and leave only 35 rows. For the event chart, keep the 45-row case filter and the NULL outcomes; do not filter NULLs out or replace them with zero. Avoid drawing an uninterrupted line through missing periods.

The relative-season axis is actual calendar seasons -2, -1, 0, +1, +2. Season 0 is the switch season and counts as post-switch; the cancelled 2019-20 season remains an explicit NULL slot where it falls inside a case window. Some later slots lie beyond the 2025-26 data window.

| School | Event label | Transition date | Kept slots | Non-NULL outcomes | Included A+B points | Pre points (-2,-1) | Post points (0,+1,+2) | NULL relative seasons |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Auburn | Under Armour → Nike (2025-26) | 2025-07-01 | 5 | 3 | 3 | 2 | 1 | +1, +2 |
| Boston College | Under Armour → Other (2021-22) | 2021-06-01 | 5 | 4 | 4 | 1 | 3 | -2 |
| California | Under Armour → Nike (2023-24) | 2023-07-01 | 5 | 5 | 5 | 2 | 3 | None |
| Cincinnati | Under Armour → Nike (2023-24) | 2023-07-01 | 5 | 5 | 5 | 2 | 3 | None |
| Georgia Tech | Other → adidas (2018-19) | 2018-07-01 | 5 | 3 | 3 | 1 | 2 | -2, +1 |
| Rutgers | adidas → Nike (2025-26) | 2025-07-01 | 5 | 3 | 3 | 2 | 1 | +1, +2 |
| Texas Tech | Under Armour → adidas (2024-25) | 2024-07-01 | 5 | 4 | 4 | 2 | 2 | +2 |
| UCLA | Under Armour → Nike (2021-22) | 2021-07-01 | 5 | 4 | 4 | 1 | 3 | -2 |
| Washington | Nike → adidas (2019-20) | 2019-07-01 | 5 | 4 | 4 | 2 | 2 | 0 |

The nine cases contain 15 included pre-switch points and 20 included post-switch points. Use `COUNT(points_pctile)` for the number of observed chart points; `COUNT(school)` counts the five calendar slots per case and therefore includes NULL-outcome slots. Do not label all five slots as five observed results.

Denver is the one excluded event: Other → Under Armour (2025-26), transition date 2025-06-03. Its five slots contain three observed outcomes, but the two pre-switch rows have unknown provider evidence. Only one post-switch row qualifies for A+B or A+B+C, so it has zero included pre points and one included post point and cannot support a before/after case.

### Switch chart values

Each non-NULL cell below is one observed `points_pctile` value, rounded to six decimals. No averaging across schools belongs in an individual case chart.

| School | -2 | -1 | 0 | +1 | +2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Auburn | 91.011236 | 94.943820 | 92.977528 | NULL | NULL |
| Boston College | NULL | 79.378531 | 69.577465 | 70.949721 | 81.179775 |
| California | 92.676056 | 94.134078 | 94.662921 | 93.539326 | 89.325843 |
| Cincinnati | 60.985915 | 59.497207 | 27.528090 | 64.887640 | 74.719101 |
| Georgia Tech | NULL | 65.517241 | 81.428571 | NULL | 87.853107 |
| Rutgers | 81.741573 | 77.808989 | 74.016854 | NULL | NULL |
| Texas Tech | 87.150838 | 87.640449 | 89.044944 | 90.449438 | NULL |
| UCLA | NULL | 96.610169 | 96.056338 | 96.368715 | 97.471910 |
| Washington | 91.954023 | 93.428571 | NULL | 90.960452 | 91.830986 |

These are descriptive case studies, not causal estimates. In particular, Cincinnati's 2023-24 value is 27.528090, compared with 59.497207 in 2022-23, and the provider switch coincided with its Big 12 move. Consult the [confounder table](../reports/switch_case_confounders.csv) when describing the case.
