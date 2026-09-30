"""Audit exported switch cases without rebuilding the analysis or its figures."""
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
BRAND_COUNT_COLUMNS = ['n_nike', 'n_adidas', 'n_under_armour', 'n_other']


@pytest.fixture(scope='module')
def cases():
    observations = pd.read_csv(ROOT/'reports/switch_case_observations.csv')
    summary = pd.read_csv(ROOT/'reports/switch_case_summary.csv')
    events = json.loads((ROOT/'data/sponsor_transition_register.json').read_text())
    return observations, summary, events


def test_ten_events_keep_five_actual_calendar_slots(cases):
    observations, summary, events = cases
    assert len(events) == 10
    assert len(observations) == 50
    assert not observations.duplicated(['school', 'season']).any()
    assert set(observations.school) == {event['school'] for event in events}
    assert observations.groupby('school').size().eq(5).all()
    for school, rows in observations.groupby('school'):
        assert set(rows.relative_season) == {-2, -1, 0, 1, 2}, school
        actual_relative_year = rows.season.str[:4].astype(int) - rows.switch_season.str[:4].astype(int)
        assert actual_relative_year.eq(rows.relative_season).all(), school
    assert len(summary) == 20
    assert not summary.duplicated(['school', 'evidence_set']).any()
    assert summary.groupby('school').evidence_set.apply(set).eq({'primary', 'sensitivity'}).all()


def test_washington_covid_switch_season_is_missing_not_zero_or_shifted(cases):
    observations, summary, _ = cases
    washington = observations.loc[observations.school.eq('Washington')]
    switch = washington.loc[washington.relative_season.eq(0)].iloc[0]
    assert switch.season == switch.switch_season == '2019-20'
    assert pd.isna(switch.points_pctile)
    assert not switch.outcome_available
    assert pd.isna(switch.brand)
    assert switch.evidence_tier == 'unknown'
    assert not switch.primary_included and not switch.sensitivity_included
    assert washington.loc[washington.season.eq('2020-21'), 'relative_season'].item() == 1
    assert washington.loc[washington.season.eq('2021-22'), 'relative_season'].item() == 2
    assert summary.loc[summary.school.eq('Washington'), 'n_post'].eq(2).all()
    assert observations.loc[observations.season.eq('2019-20'), 'points_pctile'].isna().all()


@pytest.mark.parametrize('evidence_set,tiers', [('primary', 'A+B+C'), ('sensitivity', 'A+B')])
def test_t0_counts_as_post_and_all_counts_reconcile(cases, evidence_set, tiers):
    observations, summary, _ = cases
    for row in summary.loc[summary.evidence_set.eq(evidence_set)].itertuples():
        included = observations.loc[observations.school.eq(row.school) & observations[evidence_set + '_included']]
        assert row.tiers_used == tiers
        assert row.n_pre == included.relative_season.lt(0).sum()
        assert row.n_post == included.relative_season.ge(0).sum()
        assert row.n_school_seasons == len(included) == row.n_pre + row.n_post
        assert row.n_school_seasons == row.n_nike + row.n_adidas + row.n_under_armour + row.n_other
        assert row.n_school_seasons == row.n_tier_a + row.n_tier_b + row.n_tier_c
        actual = included.brand.value_counts()
        assert row.n_nike == actual.get('Nike', 0)
        assert row.n_adidas == actual.get('adidas', 0)
        assert row.n_under_armour == actual.get('Under Armour', 0)
        assert row.n_other == actual.get('other', 0)
        assert row.usable == (row.n_pre >= 1 and row.n_post >= 1)
    # These latest switches have only t=0 observed after the transition.
    latest = summary.loc[summary.evidence_set.eq(evidence_set) & summary.school.isin(['Auburn', 'Rutgers'])]
    assert latest.n_post.eq(1).all()
    assert latest.usable.all()


def test_denver_has_no_invented_pre_provider_or_change_estimate(cases):
    observations, summary, _ = cases
    pre = observations.loc[observations.school.eq('Denver') & observations.relative_season.lt(0)]
    assert set(pre.season) == {'2023-24', '2024-25'}
    assert pre.outcome_available.all()
    assert pre.points_pctile.notna().all()
    assert pre.brand.isna().all()
    assert pre.evidence_tier.eq('unknown').all()
    assert not pre.primary_included.any()
    assert not pre.sensitivity_included.any()
    denver = summary.loc[summary.school.eq('Denver')]
    assert not denver.usable.any()
    assert denver.n_pre.eq(0).all() and denver.n_post.eq(1).all()
    assert denver.pre_mean_points_pctile.isna().all()
    assert denver.descriptive_change.isna().all()
    assert denver.reason.str.contains('No covered pre-switch season', regex=False).all()
    assert summary.groupby('evidence_set').usable.sum().eq(9).all()


def test_current_case_results_match_across_evidence_sets(cases):
    observations, summary, _ = cases
    included = observations.loc[observations.primary_included]
    assert included.evidence_tier.eq('A').all()
    assert observations.primary_included.equals(observations.sensitivity_included)
    comparable = ['school', 'usable', 'n_pre', 'n_post', 'n_school_seasons', 'n_per_brand',
                  'pre_mean_points_pctile', 'post_mean_points_pctile', 'descriptive_change',
                  'n_tier_a', 'n_tier_b', 'n_tier_c'] + BRAND_COUNT_COLUMNS
    primary = summary.loc[summary.evidence_set.eq('primary'), comparable].sort_values('school').reset_index(drop=True)
    sensitivity = summary.loc[summary.evidence_set.eq('sensitivity'), comparable].sort_values('school').reset_index(drop=True)
    pd.testing.assert_frame_equal(primary, sensitivity)


def test_missing_outcomes_are_never_included(cases):
    observations, _, _ = cases
    missing = observations.loc[~observations.outcome_available]
    assert not missing.empty
    assert missing.points_pctile.isna().all()
    assert not missing.primary_included.any()
    assert not missing.sensitivity_included.any()
