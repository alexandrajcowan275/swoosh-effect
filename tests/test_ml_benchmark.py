"""Temporal leakage, sample comparability, and uncertainty regressions."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.ml_features import (build_features, evidence_date, feature_columns,
                             load_features, rolling_folds, temporal_split)
from src.ml_benchmark import (bootstrap_metrics, errors, fit_model,
                              permutation_importance, predict, prediction_rows, tune)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def raw():
    panel, sports, sponsors, mapping = [], [], [], []
    for i in range(12):
        school = f'School {i}'
        mapping.append(dict(school_raw=school, school_id=f's{i}'))
        for year in [2017, 2018, 2020, 2021, 2022, 2023, 2024, 2025]:
            season = f'{year}-{str(year+1)[-2:]}'
            score = 15 + i*5 + (year-2017)*.5
            panel.append(dict(school_id=f's{i}', school=school, season=season,
                              panel_points_pctile=score, conference='East' if i<6 else 'West'))
            for sport in ['Baseball', "Women's Rowing"]:
                sports.append(dict(school=school, season=season, sport=sport, sport_points=score))
            sponsors.append(dict(school_id=f's{i}', season=season, brand='Nike' if i<6 else 'adidas',
                                 evidence_tier='A', source_url=f'https://example.org/news/{year}/7/1/provider',
                                 source_date=None, snapshot_date=None))
    return tuple(map(pd.DataFrame, [panel, sports, mapping, sponsors]))


def test_exact_calendar_lags_and_no_current_outcome_or_conference_features(raw):
    f = build_features(*raw)
    assert f.loc[f.year.eq(2020), 'points_pctile_lag1'].isna().all()
    assert f.loc[f.year.eq(2021), 'points_pctile_lag2'].isna().all()
    numeric, categorical = feature_columns(f)
    assert not {'points_pctile', 'rank', 'total_points', 'school_id', 'conference'} & set(numeric + categorical)
    target = f[(f.school_id == 's0') & (f.year == 2024)].iloc[0]
    assert target.points_pctile_lag1 == 18
    assert target.lag1_source_year == 2023 and target.lag2_source_year == 2022


def test_same_and_future_season_mutations_cannot_change_earlier_predictors(raw):
    panel, sports, mapping, sponsors = raw
    before = build_features(*raw)
    panel.loc[panel.season.ge('2024'), ['panel_points_pctile', 'conference']] = [0, 'Future Conference']
    sports.loc[sports.season.ge('2024'), 'sport_points'] = 999
    after = build_features(panel, sports, mapping, sponsors)
    numeric, categorical = feature_columns(before)
    cols = ['school_id', 'season'] + numeric + categorical
    pd.testing.assert_frame_equal(before.loc[before.year.le(2024), cols],
                                  after.loc[after.year.le(2024), cols])


def test_brand_requires_preseason_direct_dated_evidence(raw):
    panel, sports, mapping, sponsors = raw
    mask = sponsors.season.eq('2024-25')
    sponsors.loc[mask & sponsors.school_id.eq('s0'), 'source_url'] = 'https://example.org/undated'
    sponsors.loc[mask & sponsors.school_id.eq('s1'), 'source_date'] = '2024-08-01'
    sponsors.loc[mask & sponsors.school_id.eq('s2'), 'evidence_tier'] = 'C'
    sponsors.loc[mask & sponsors.school_id.eq('s3'), 'snapshot_date'] = '2024-10-01'
    f = build_features(panel, sports, mapping, sponsors)
    q = f[f.year.eq(2024)].set_index('school_id')
    assert q.loc[['s0', 's1', 's2', 's3'], 'brand'].eq('Unknown').all()
    assert q.loc['s4', 'brand'] == 'Nike'
    assert q.loc['s4', 'brand_date_basis'] == 'date_in_source_url'
    assert set(f.brand_evidence_tier) <= {'A', 'B', 'unknown'}
    assert evidence_date({'source_url': 'https://example.org/2024/2/30/x'})[0] is None
    assert evidence_date({'source_url': 'https://example.org/2024/x'})[0] is None


def test_entire_seasons_are_held_out_and_all_origins_are_earlier(raw):
    train, test = temporal_split(build_features(*raw))
    assert set(test.year) == {2024, 2025}
    assert train.year.max() == 2023
    folds = list(rolling_folds(train))
    assert [int(v.year.iloc[0]) for _, v in folds] == [2021, 2022, 2023]
    for t, v in folds:
        assert t.year.max() < v.year.min()
        assert v.year.nunique() == 1
        assert not set(t.index) & set(v.index)


def test_preprocessing_is_fit_on_train_and_ignores_unseen_categories(raw):
    train, test = temporal_split(build_features(*raw))
    test['conference_prior'] = 'Unseen Holdout Conference'
    model = fit_model(train, 'lagged_ols')
    categories = model.named_steps['unseen'].kw_args['categories']
    assert 'Unseen Holdout Conference' not in categories['conference_prior']
    assert np.isfinite(predict(model, test)).all()
    numeric, _ = feature_columns(train, ols=True)
    actual = model.named_steps['preprocess'].named_transformers_['numeric'].statistics_
    np.testing.assert_allclose(actual, train[numeric].median().to_numpy())


def test_small_booster_tuning_never_sees_holdout_and_runs_importance(raw):
    train, test = temporal_split(build_features(*raw))
    grid = [dict(n_estimators=5, num_leaves=3, min_child_samples=2)]
    params, cv = tune(train, grid=grid)
    assert cv.validation_year.max() == 2023
    assert (cv.train_max_year < cv.validation_year).all()
    model = fit_model(train, 'lightgbm', params)
    p = predict(model, test)
    assert len(p) == len(test) and np.isfinite(p).all()
    assert ((p >= 0) & (p <= 100)).all()
    importance = permutation_importance(model, test, repeats=3)
    assert set(importance.level) == {'individual', 'grouped'}
    assert importance.loc[importance.feature.eq('brand')].shape[0] == 2


def test_paired_school_bootstrap_is_reproducible_and_zero_for_identical_predictions(raw):
    _, test = temporal_split(build_features(*raw))
    predicted = test.points_pctile_lag1.to_numpy()
    frames = [prediction_rows(test, name, predicted) for name in
              ['naive', 'lagged_ols', 'lightgbm', 'lightgbm_no_brand']]
    predictions = pd.concat(frames, ignore_index=True)
    metrics, differences = bootstrap_metrics(predictions, repeats=100, seed=7)
    again, _ = bootstrap_metrics(predictions, repeats=100, seed=7)
    pd.testing.assert_frame_equal(metrics, again)
    assert differences[['error_difference', 'ci_low', 'ci_high']].eq(0).all().all()
    assert metrics[metrics.season.eq('pooled')].n.eq(24).all()
    assert metrics[metrics.season.eq('pooled')].n_schools.eq(12).all()
    mae, rmse = errors([0, 10], [0, 8])
    assert mae == 1 and rmse == pytest.approx(np.sqrt(2))


def test_real_feature_audit_preserves_unknowns_and_historical_cutoffs():
    features = load_features(ROOT)
    train, test = temporal_split(features)
    known = features[features.brand.ne('Unknown')]
    assert (known.brand_source_date < known.cutoff_date).all()
    assert known.brand_evidence_tier.isin(['A', 'B']).all()
    assert features.brand.eq('Unknown').any()
    for lag in (1, 2):
        present = features[f'lag{lag}_source_year'].notna()
        assert (features.loc[present, f'lag{lag}_source_year'] == features.loc[present, 'year']-lag).all()
    assert set(test.season) == {'2024-25', '2025-26'}
    assert train.year.max() < test.year.min()


def test_bootstrap_rejects_unmatched_school_season_rows(raw):
    _, test = temporal_split(build_features(*raw))
    a = prediction_rows(test, 'naive', test.points_pctile_lag1)
    b = prediction_rows(test.iloc[1:], 'lightgbm', test.iloc[1:].points_pctile_lag1)
    with pytest.raises(ValueError, match='identical unique school-season'):
        bootstrap_metrics(pd.concat([a, b]), repeats=10)


def test_committed_metrics_reconcile_to_prediction_errors():
    p = pd.read_csv(ROOT/'reports/ml/predictions.csv')
    metrics = pd.read_csv(ROOT/'reports/ml/metrics.csv')
    for row in metrics.itertuples():
        selected = p[p.model.eq(row.model)]
        if row.season != 'pooled':
            selected = selected[selected.season.eq(row.season)]
        assert len(selected) == row.n
        assert selected.school_id.nunique() == row.n_schools
        mae, rmse = errors(selected.points_pctile, selected.prediction)
        assert row.estimate == pytest.approx(mae if row.metric == 'MAE' else rmse, abs=1e-8)
        assert row.ci_low <= row.estimate <= row.ci_high
    assert set(p.season) == {'2024-25', '2025-26'}
    keys = p.groupby('model').apply(lambda g: set(zip(g.school_id, g.season)), include_groups=False)
    assert all(key == keys.iloc[0] for key in keys)


def test_report_records_the_exact_input_bytes():
    import hashlib
    import json
    metadata = json.loads((ROOT/'reports/ml/metadata.json').read_text())
    for name, expected in metadata['input_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
