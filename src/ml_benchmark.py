"""Reproducible one-season-ahead LightGBM benchmark, never a causal brand model.

Run `python -m src.ml_benchmark`. Hyperparameters are chosen exclusively by
expanding-origin MAE on the development years. The last two seasons are held
out together; the fitted models never refit on their outcomes. The second test
year may use the observed first test year's lag, as a one-step forecast would.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
from lightgbm import LGBMRegressor

from src.ml_features import (ROOT, META, feature_columns, load_features,
                             rolling_folds, temporal_split)

SEED = 20260930
GRID = [dict(n_estimators=100, num_leaves=7, min_child_samples=30),
        dict(n_estimators=250, num_leaves=7, min_child_samples=30),
        dict(n_estimators=100, num_leaves=15, min_child_samples=40),
        dict(n_estimators=250, num_leaves=15, min_child_samples=40)]
MODELS = ['naive', 'lagged_ols', 'lightgbm', 'lightgbm_no_brand']


def map_unseen(frame, categories):
    frame = frame.copy()
    for column, levels in categories.items():
        frame[column] = frame[column].where(frame[column].isin(levels), 'Unknown')
    return frame


def fit_model(train, kind, params=None):
    """Fit all imputation/encoding on this training fold only; no global fit."""
    numeric, categorical = feature_columns(train, ols=kind == 'lagged_ols',
                                           brand=kind != 'lightgbm_no_brand')
    levels = {c: ['Unknown'] + sorted(set(train[c].dropna()) - {'Unknown'}) for c in categorical}
    prep = ColumnTransformer([
        ('numeric', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True), numeric),
        ('categorical', OneHotEncoder(categories=list(levels.values()), drop='first',
                                      handle_unknown='ignore', sparse_output=False), categorical),
    ], remainder='drop')
    if kind == 'lagged_ols':
        estimator = LinearRegression()
    else:
        estimator = LGBMRegressor(objective='regression', learning_rate=.05,
                                 random_state=SEED, n_jobs=1, deterministic=True,
                                 force_col_wise=True, verbosity=-1, **(params or GRID[0]))
    model = Pipeline([('unseen', FunctionTransformer(map_unseen, kw_args={'categories': levels})),
                      ('preprocess', prep), ('model', estimator)])
    model.fit(train, train.points_pctile)
    return model


def predict(model, frame):
    # LightGBM's sklearn adapter warns when ColumnTransformer supplies arrays;
    # column order is fixed by the fitted transformer, not inferred at prediction.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='X does not have valid feature names')
        return np.clip(model.predict(frame), 0, 100)


def errors(actual, predicted):
    residual = np.asarray(actual) - np.asarray(predicted)
    return float(np.abs(residual).mean()), float(np.sqrt(np.square(residual).mean()))


def tune(train, *, kind='lightgbm', grid=None):
    records = []
    grid = GRID if grid is None else grid
    for candidate, params in enumerate(grid):
        for earlier, later in rolling_folds(train):
            model = fit_model(earlier, kind, params)
            mae, rmse = errors(later.points_pctile, predict(model, later))
            records.append(dict(model=kind, candidate=candidate, validation_year=int(later.year.iloc[0]),
                                train_max_year=int(earlier.year.max()), n_train=len(earlier),
                                n_validation=len(later), mae=mae, rmse=rmse,
                                parameters=json.dumps(params, sort_keys=True)))
    results = pd.DataFrame(records)
    scores = results.groupby('candidate').mae.mean()  # equal weight to each season
    winner = int(scores.idxmin())
    results['selected'] = results.candidate.eq(winner)
    return grid[winner], results


def prediction_rows(frame, name, predicted):
    result = frame[META + ['brand']].copy()
    result['model'] = name
    result['prediction'] = predicted
    result['absolute_error'] = np.abs(result.points_pctile - result.prediction)
    result['squared_error'] = np.square(result.points_pctile - result.prediction)
    return result


def bootstrap_metrics(predictions, *, repeats=2000, seed=SEED):
    """School-cluster percentile CIs, paired across models, conditional on fits.

    Resample school IDs with replacement, retaining both held-out years for each
    sampled school. These intervals exclude refit and future-season uncertainty.
    """
    expected = None
    for _, frame in predictions.groupby('model'):
        keys = set(zip(frame.school_id, frame.season))
        if len(keys) != len(frame) or (expected is not None and keys != expected):
            raise ValueError('All models must use identical unique school-season rows')
        expected = keys
    metrics, comparisons = [], []
    for label in ['pooled', *sorted(predictions.season.unique())]:
        sample = predictions if label == 'pooled' else predictions[predictions.season.eq(label)]
        schools = sorted(sample.school_id.unique())
        rng = np.random.default_rng(seed)
        weights = rng.multinomial(len(schools), np.full(len(schools), 1 / len(schools)), size=repeats)
        draws = {}
        estimates = {}
        for name, frame in sample.groupby('model', sort=True):
            sums = frame.groupby('school_id')[['absolute_error', 'squared_error']].sum().reindex(schools)
            counts = frame.groupby('school_id').size().reindex(schools).to_numpy()
            if sums.isna().any().any():
                raise ValueError('All models must use the same schools')
            denominator = weights @ counts
            draws[name] = {'MAE': (weights @ sums.absolute_error.to_numpy()) / denominator,
                           'RMSE': np.sqrt((weights @ sums.squared_error.to_numpy()) / denominator)}
            estimates[name] = dict(zip(['MAE', 'RMSE'], errors(frame.points_pctile, frame.prediction)))
            for metric in ['MAE', 'RMSE']:
                lo, hi = np.quantile(draws[name][metric], [.025, .975])
                metrics.append(dict(season=label, model=name, metric=metric,
                                    estimate=estimates[name][metric], ci_low=lo, ci_high=hi,
                                    n=len(frame), n_schools=len(schools), bootstrap_repeats=repeats))
        for name in sorted(set(draws) - {'naive'}):
            for metric in ['MAE', 'RMSE']:
                delta = draws[name][metric] - draws['naive'][metric]
                lo, hi = np.quantile(delta, [.025, .975])
                comparisons.append(dict(season=label, model=name, reference='naive', metric=metric,
                                        error_difference=estimates[name][metric] - estimates['naive'][metric],
                                        ci_low=lo, ci_high=hi))
        for metric in ['MAE', 'RMSE']:
            delta = draws['lightgbm'][metric] - draws['lightgbm_no_brand'][metric]
            lo, hi = np.quantile(delta, [.025, .975])
            comparisons.append(dict(season=label, model='lightgbm', reference='lightgbm_no_brand', metric=metric,
                                    error_difference=estimates['lightgbm'][metric] - estimates['lightgbm_no_brand'][metric],
                                    ci_low=lo, ci_high=hi))
    return pd.DataFrame(metrics), pd.DataFrame(comparisons)


def permutation_importance(model, test, *, repeats=30):
    """Shuffle raw features within each test season, keeping brand dummies together.

    Repeat quantiles show permutation variability, not confidence intervals on a
    causal effect. Correlated predictors can share importance. Aggregate groups
    supplement individual-column rankings and are never mixed in the same rank.
    """
    numeric, categorical = feature_columns(test)
    individual = {c: [c] for c in numeric + categorical}
    grouped = {'prior_performance': ['points_pctile_lag1', 'points_pctile_lag2'],
               'prior_sport_points': [c for c in numeric if c.startswith('sport_lag1__')],
               'brand': ['brand'], 'conference_prior': ['conference_prior']}
    baseline = errors(test.points_pctile, predict(model, test))[0]
    records = []
    for level, groups in [('individual', individual), ('grouped', grouped)]:
        for feature, columns in groups.items():
            differences = []
            rng = np.random.default_rng(SEED)
            for _ in range(repeats):
                shuffled = test.copy()
                for _, indices in test.groupby('year').groups.items():
                    permuted = rng.permutation(indices)
                    shuffled.loc[indices, columns] = test.loc[permuted, columns].to_numpy()
                differences.append(errors(test.points_pctile, predict(model, shuffled))[0] - baseline)
            lo, hi = np.quantile(differences, [.025, .975])
            records.append(dict(level=level, feature=feature, mean_mae_increase=np.mean(differences),
                                std_mae_increase=np.std(differences, ddof=1),
                                shuffle_p025=lo, shuffle_p975=hi, repeats=repeats))
    result = pd.DataFrame(records)
    result['rank'] = result.groupby('level').mean_mae_increase.rank(method='min', ascending=False).astype(int)
    return result.sort_values(['level', 'rank', 'feature'])


def write_report(out, train, test, metrics, comparisons, importance, counts, metadata):
    lines = ['# Predicting next season’s athletic performance', '',
             'This is a forecasting benchmark across the eligible observed-ever D1 panel, not a causal test of apparel sponsorship. Unknown brands remain a separate category; they are never recoded to Other.', '',
             f'Train: {", ".join(sorted(train.season.unique()))} ({len(train)} school-seasons). '
             f'Holdout: {", ".join(sorted(test.season.unique()))} ({len(test)} school-seasons, {test.school_id.nunique()} schools).', '',
             'The model is frozen after 2023-24. For the 2025-26 one-step forecast, 2024-25 observations are available as lags but never used to refit or select hyperparameters. All four models use identical test rows. Outcomes and errors are percentile points on a 0–100 scale.', '',
             '## Held-out accuracy', '',
             '| Season | Model | n | MAE [95% CI] | RMSE [95% CI] |',
             '|---|---|---:|---:|---:|']
    for season in ['pooled', *sorted(test.season.unique())]:
        for model in MODELS:
            q = metrics[(metrics.season == season) & (metrics.model == model)].set_index('metric')
            vals = [f'{q.loc[m,"estimate"]:.3f} [{q.loc[m,"ci_low"]:.3f}, {q.loc[m,"ci_high"]:.3f}]' for m in ['MAE', 'RMSE']]
            lines.append(f'| {season} | {model} | {int(q.iloc[0]["n"])} | {vals[0]} | {vals[1]} |')
    lines += ['', 'Intervals use 2,000 paired school-cluster bootstrap resamples (both test seasons retained per sampled school), conditional on the fitted models. They do not capture training uncertainty or variation across future season shocks; there are only two held-out seasons.', '',
              '## Does the ensemble improve on the baselines?', '',
              'Negative paired error differences favor the named model. See `paired_comparisons.csv` for every comparison and season.', '',
              '| Model | Reference | MAE difference [95% CI] | RMSE difference [95% CI] |', '|---|---|---:|---:|']
    pairs = comparisons[comparisons.season.eq('pooled')]
    for (model, reference), group in pairs.groupby(['model', 'reference']):
        q = group.set_index('metric')
        vals = [f'{q.loc[m,"error_difference"]:.3f} [{q.loc[m,"ci_low"]:.3f}, {q.loc[m,"ci_high"]:.3f}]' for m in ['MAE', 'RMSE']]
        lines.append(f'| {model} | {reference} | {vals[0]} | {vals[1]} |')
    pooled = metrics[(metrics.season == 'pooled') & (metrics.metric == 'MAE')].set_index('model')
    winner = pooled.estimate.idxmin()
    lines += ['', f'The lowest pooled held-out MAE belongs to **{winner}**. This ranking is a result, not a model-selection input; the holdout was not used for tuning.', '',
              '## Brand importance', '', '| Feature | Individual rank | Increase in held-out MAE after permutation |', '|---|---:|---:|']
    single = importance[importance.level.eq('individual')].set_index('feature')
    for feature in ['brand', 'points_pctile_lag1', 'points_pctile_lag2', 'conference_prior']:
        row = single.loc[feature]
        lines.append(f'| {feature} | {int(row["rank"])}/{len(single)} | {row.mean_mae_increase:.4f} |')
    lines += ['', 'Ranks use the minimum rank for ties; zero importance can tie across several unused fields.', '', 'Permutation uses 30 repetitions within each held-out season, shuffling each raw field before encoding. Brand is permuted as one categorical field, not separate dummy columns. Quantiles in `permutation_importance.csv` describe shuffle variability, not statistical confidence. `season_year` is constant within each season, so its permutation importance is structurally zero and not an estimate of temporal importance.', '',
              'Prior performance and sport scores are correlated, so importance can be shared between them. The grouped importance rows permute both percentile lags together and all prior-sport columns together. A separately tuned model omitting brand is also reported; neither method identifies a causal brand effect.', '',
              '## Counts and evidence', '', '| Sample | Pre-season brand | Tier | n school-seasons |', '|---|---|---|---:|']
    for row in counts.itertuples():
        lines.append(f'| {row.sample} | {row.brand} | {row.brand_evidence_tier} | {row.n} |')
    lines += ['', '## Feature availability and leakage controls', '',
              '- Target: `panel_points_pctile` from the audited D1 panel, renamed `points_pctile` for this benchmark. Eligibility and missing published rank remain as in the existing research.',
              '- Percentile lags use exact calendar years. No 2018-19 → 2020-21 bridge. Rows without t−1 are excluded from every model; t−2 may be missing.',
              '- `conference_prior` is the prior season’s printed conference, with Pac 12 spelling normalized. It is a pre-season proxy, not the target year’s retrospectively observed conference. No neighbor-based future imputation is used.',
              '- `brand` uses only direct A/B evidence covering the target season and dated strictly before August 1 of that year. Explicit dates are preferred; a complete YYYY/M/D source URL path can supply a labeled publication-date proxy. Archive dates can only delay availability. Undated, late, absent, and Tier C assignments become Unknown. No continuity inference is a model feature.',
              '- Prior sport points are the previous calendar season’s published scores across sports. Missing/excluded cells stay null; they are not converted into invented zero scores or uncertain final contributions. The sport vocabulary is fixed from the earliest source year.',
              '- `season_year` is a known calendar trend. Predictive lagged OLS uses lag1 + brand + prior-conference indicators + this linear trend. The original retrospective OLS season fixed effects cannot estimate unseen future seasons, so this is explicitly a forecast adaptation. OLS is not refit on test outcomes.',
              '- LightGBM adds lag2 and prior-sport features. Four fixed small configurations are selected by mean MAE across expanding-origin development folds; all imputation and encoding are fitted afresh within each fold. The no-brand ablation is tuned independently on the same development folds.',
              '- No random train/test split, school ID feature, same-season rank/total/sport feature, outcome-based feature selection, holdout early stopping, or holdout tuning. Predictions from every model are restricted to the valid 0–100 range.', '',
              '## Limitations', '',
              'The cohort is all schools present at least once in the existing standings database, not a prospective D1 census. Brand research covers a selected subset and the stricter date rule masks many researched assignments; importance here cannot establish that apparel brands generally do not matter. Date-bearing URLs and frozen historical scores are publication proxies, not a fully versioned as-of archive: revisions to prior-season source values cannot be reconstructed. Sports reflect scoring participation and available reports, not complete program offerings. Two held-out seasons provide limited evidence about future performance.', '',
              '## Reproduce and audit', '',
              '`python -m src.ml_benchmark` regenerates this report and CSVs from committed inputs. `./run.sh --offline` also runs it. The random seed is fixed, LightGBM uses one CPU thread and deterministic mode, and dependencies are pinned.', '',
              'See `metadata.json` for input hashes, selected parameters and versions; `rolling_cv.csv` for every tuning fold; `rolling_baselines.csv` for naive/OLS development scores; `predictions.csv` for held-out predictions; `feature_availability.csv` for dated/masked evidence and lag years; `sample_counts.csv` and `exclusions.csv` for denominators.', '',
              '[LightGBM parameters](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html) · [Permutation importance](https://scikit-learn.org/stable/modules/permutation_importance.html)', '',
              'Independent student project. Not affiliated with or endorsed by Nike, Inc.', '']
    (out/'README.md').write_text('\n'.join(lines))


def run(root=ROOT, *, bootstrap_repeats=2000, permutation_repeats=30):
    out = root/'reports/ml'; out.mkdir(parents=True, exist_ok=True)
    features = load_features(root)
    train, test = temporal_split(features)
    tuning, settings, fitted = [], {}, {}
    for name in ['lightgbm', 'lightgbm_no_brand']:
        params, cv = tune(train, kind=name)
        tuning.append(cv); settings[name] = params
        fitted[name] = fit_model(train, name, params)
    fitted['lagged_ols'] = fit_model(train, 'lagged_ols')
    predictions = [prediction_rows(test, 'naive', test.points_pctile_lag1.to_numpy())]
    for name in MODELS[1:]:
        predictions.append(prediction_rows(test, name, predict(fitted[name], test)))
    predictions = pd.concat(predictions, ignore_index=True)
    metrics, comparisons = bootstrap_metrics(predictions, repeats=bootstrap_repeats)
    importance = permutation_importance(fitted['lightgbm'], test, repeats=permutation_repeats)
    baseline_cv = []
    for earlier, later in rolling_folds(train):
        for name in ['naive', 'lagged_ols']:
            pred = later.points_pctile_lag1 if name == 'naive' else predict(fit_model(earlier, name), later)
            mae, rmse = errors(later.points_pctile, pred)
            baseline_cv.append(dict(model=name, train_max_year=int(earlier.year.max()), validation_year=int(later.year.iloc[0]),
                                    n_train=len(earlier), n_validation=len(later), mae=mae, rmse=rmse))
    count_frames = []
    for sample, frame in [('train', train), ('holdout', test), *list(test.groupby('season'))]:
        c = frame.groupby(['brand', 'brand_evidence_tier']).size().rename('n').reset_index()
        c.insert(0, 'sample', sample); count_frames.append(c)
    counts = pd.concat(count_frames, ignore_index=True)
    exclusions = features.groupby('season').agg(total_rows=('school_id', 'size'),
            eligible_with_lag1=('points_pctile_lag1', lambda x: int(x.notna().sum())),
            known_preseason_brand=('brand', lambda x: int(x.ne('Unknown').sum()))).reset_index()
    exclusions['excluded_missing_lag1'] = exclusions.total_rows - exclusions.eligible_with_lag1
    tables = dict(metrics=metrics, paired_comparisons=comparisons, predictions=predictions,
                  rolling_cv=pd.concat(tuning, ignore_index=True), rolling_baselines=pd.DataFrame(baseline_cv),
                  permutation_importance=importance, sample_counts=counts, exclusions=exclusions,
                  feature_availability=features[META + ['brand', 'conference_prior', 'points_pctile_lag1', 'points_pctile_lag2']])
    for name, frame in tables.items():
        frame.to_csv(out/f'{name}.csv', index=False, float_format='%.10f')
    import lightgbm, sklearn
    inputs = ['data/processed/analysis_panel.csv', 'data/processed/sport_points_long.csv',
              'data/processed/sponsor_seasons.csv', 'data/school_name_map.csv']
    metadata = dict(seed=SEED, train_seasons=sorted(train.season.unique()),
                    test_seasons=sorted(test.season.unique()), n_train=len(train), n_test=len(test),
                    selected_parameters=settings, parameter_grid=GRID,
                    bootstrap_repeats=bootstrap_repeats, permutation_repeats=permutation_repeats,
                    versions=dict(lightgbm=lightgbm.__version__, sklearn=sklearn.__version__, numpy=np.__version__, pandas=pd.__version__),
                    input_sha256={name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in inputs},
                    forecast='one-step, fixed model, observed prior test outcome allowed as next-year lag; no refitting',
                    brand_rule='A/B only with source date strictly before target-year August 1; URL-date proxies labeled; no C')
    (out/'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    write_report(out, train, test, metrics, comparisons, importance, counts, metadata)
    print(metrics[metrics.season.eq('pooled')].to_string(index=False))
    print(importance[importance.feature.isin(['brand', 'points_pctile_lag1', 'points_pctile_lag2'])].to_string(index=False))
    return tables


if __name__ == '__main__':
    run()
