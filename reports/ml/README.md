# Predicting next season’s athletic performance

This is a forecasting benchmark across the eligible observed-ever D1 panel, not a causal test of apparel sponsorship. Unknown brands remain a separate category; they are never recoded to Other.

Train: 2018-19, 2021-22, 2022-23, 2023-24 (1413 school-seasons). Holdout: 2024-25, 2025-26 (712 school-seasons, 356 schools).

The model is frozen after 2023-24. For the 2025-26 one-step forecast, 2024-25 observations are available as lags but never used to refit or select hyperparameters. All four models use identical test rows. Outcomes and errors are percentile points on a 0–100 scale.

## Held-out accuracy

| Season | Model | n | MAE [95% CI] | RMSE [95% CI] |
|---|---|---:|---:|---:|
| pooled | naive | 712 | 11.078 [10.174, 12.005] | 15.659 [14.559, 16.720] |
| pooled | lagged_ols | 712 | 11.117 [10.384, 11.862] | 14.400 [13.518, 15.249] |
| pooled | lightgbm | 712 | 11.183 [10.419, 11.946] | 14.581 [13.666, 15.474] |
| pooled | lightgbm_no_brand | 712 | 11.183 [10.419, 11.946] | 14.581 [13.666, 15.474] |
| 2024-25 | naive | 356 | 11.224 [10.086, 12.422] | 15.924 [14.373, 17.445] |
| 2024-25 | lagged_ols | 356 | 10.993 [10.031, 12.008] | 14.456 [13.221, 15.629] |
| 2024-25 | lightgbm | 356 | 10.970 [10.020, 11.951] | 14.404 [13.225, 15.646] |
| 2024-25 | lightgbm_no_brand | 356 | 10.970 [10.020, 11.951] | 14.404 [13.225, 15.646] |
| 2025-26 | naive | 356 | 10.931 [9.810, 12.066] | 15.389 [14.001, 16.755] |
| 2025-26 | lagged_ols | 356 | 11.241 [10.318, 12.127] | 14.345 [13.206, 15.426] |
| 2025-26 | lightgbm | 356 | 11.396 [10.424, 12.391] | 14.755 [13.569, 15.956] |
| 2025-26 | lightgbm_no_brand | 356 | 11.396 [10.424, 12.391] | 14.755 [13.569, 15.956] |

Intervals use 2,000 paired school-cluster bootstrap resamples (both test seasons retained per sampled school), conditional on the fitted models. They do not capture training uncertainty or variation across future season shocks; there are only two held-out seasons.

## Does the ensemble improve on the baselines?

Negative paired error differences favor the named model. See `paired_comparisons.csv` for every comparison and season.

| Model | Reference | MAE difference [95% CI] | RMSE difference [95% CI] |
|---|---|---:|---:|
| lagged_ols | naive | 0.039 [-0.454, 0.543] | -1.258 [-1.743, -0.770] |
| lightgbm | lightgbm_no_brand | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| lightgbm | naive | 0.105 [-0.403, 0.611] | -1.078 [-1.638, -0.495] |
| lightgbm_no_brand | naive | 0.105 [-0.403, 0.611] | -1.078 [-1.638, -0.495] |

The lowest pooled held-out MAE belongs to **naive**. This ranking is a result, not a model-selection input; the holdout was not used for tuning.

## Brand importance

| Feature | Individual rank | Increase in held-out MAE after permutation |
|---|---:|---:|
| brand | 22/43 | 0.0000 |
| points_pctile_lag1 | 1/43 | 16.9697 |
| points_pctile_lag2 | 2/43 | 0.8356 |
| conference_prior | 42/43 | -0.0108 |

Ranks use the minimum rank for ties; zero importance can tie across several unused fields.

Permutation uses 30 repetitions within each held-out season, shuffling each raw field before encoding. Brand is permuted as one categorical field, not separate dummy columns. Quantiles in `permutation_importance.csv` describe shuffle variability, not statistical confidence. `season_year` is constant within each season, so its permutation importance is structurally zero and not an estimate of temporal importance.

Prior performance and sport scores are correlated, so importance can be shared between them. The grouped importance rows permute both percentile lags together and all prior-sport columns together. A separately tuned model omitting brand is also reported; neither method identifies a causal brand effect.

## Counts and evidence

| Sample | Pre-season brand | Tier | n school-seasons |
|---|---|---|---:|
| train | Nike | A | 51 |
| train | Nike | B | 1 |
| train | Under Armour | A | 12 |
| train | Unknown | unknown | 1316 |
| train | adidas | A | 30 |
| train | other | A | 3 |
| holdout | Nike | A | 32 |
| holdout | Under Armour | A | 5 |
| holdout | Unknown | unknown | 661 |
| holdout | adidas | A | 12 |
| holdout | other | A | 2 |
| 2024-25 | Nike | A | 15 |
| 2024-25 | Under Armour | A | 2 |
| 2024-25 | Unknown | unknown | 332 |
| 2024-25 | adidas | A | 6 |
| 2024-25 | other | A | 1 |
| 2025-26 | Nike | A | 17 |
| 2025-26 | Under Armour | A | 3 |
| 2025-26 | Unknown | unknown | 329 |
| 2025-26 | adidas | A | 6 |
| 2025-26 | other | A | 1 |

## Feature availability and leakage controls

- Target: `panel_points_pctile` from the audited D1 panel, renamed `points_pctile` for this benchmark. Eligibility and missing published rank remain as in the existing research.
- Percentile lags use exact calendar years. No 2018-19 → 2020-21 bridge. Rows without t−1 are excluded from every model; t−2 may be missing.
- `conference_prior` is the prior season’s printed conference, with Pac 12 spelling normalized. It is a pre-season proxy, not the target year’s retrospectively observed conference. No neighbor-based future imputation is used.
- `brand` uses only direct A/B evidence covering the target season and dated strictly before August 1 of that year. Explicit dates are preferred; a complete YYYY/M/D source URL path can supply a labeled publication-date proxy. Archive dates can only delay availability. Undated, late, absent, and Tier C assignments become Unknown. No continuity inference is a model feature.
- Prior sport points are the previous calendar season’s published scores across sports. Missing/excluded cells stay null; they are not converted into invented zero scores or uncertain final contributions. The sport vocabulary is fixed from the earliest source year.
- `season_year` is a known calendar trend. Predictive lagged OLS uses lag1 + brand + prior-conference indicators + this linear trend. The original retrospective OLS season fixed effects cannot estimate unseen future seasons, so this is explicitly a forecast adaptation. OLS is not refit on test outcomes.
- LightGBM adds lag2 and prior-sport features. Four fixed small configurations are selected by mean MAE across expanding-origin development folds; all imputation and encoding are fitted afresh within each fold. The no-brand ablation is tuned independently on the same development folds.
- No random train/test split, school ID feature, same-season rank/total/sport feature, outcome-based feature selection, holdout early stopping, or holdout tuning. Predictions from every model are restricted to the valid 0–100 range.

## Limitations

The cohort is all schools present at least once in the existing standings database, not a prospective D1 census. Brand research covers a selected subset and the stricter date rule masks many researched assignments; importance here cannot establish that apparel brands generally do not matter. Date-bearing URLs and frozen historical scores are publication proxies, not a fully versioned as-of archive: revisions to prior-season source values cannot be reconstructed. Sports reflect scoring participation and available reports, not complete program offerings. Two held-out seasons provide limited evidence about future performance.

## Reproduce and audit

`python -m src.ml_benchmark` regenerates this report and CSVs from committed inputs. `./run.sh --offline` also runs it. The random seed is fixed, LightGBM uses one CPU thread and deterministic mode, and dependencies are pinned.

See `metadata.json` for input hashes, selected parameters and versions; `rolling_cv.csv` for every tuning fold; `rolling_baselines.csv` for naive/OLS development scores; `predictions.csv` for held-out predictions; `feature_availability.csv` for dated/masked evidence and lag years; `sample_counts.csv` and `exclusions.csv` for denominators.

[LightGBM parameters](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html) · [Permutation importance](https://scikit-learn.org/stable/modules/permutation_importance.html)

Independent student project. Not affiliated with or endorsed by Nike, Inc.
