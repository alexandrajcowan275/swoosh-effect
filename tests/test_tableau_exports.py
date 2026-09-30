"""Exports must reconcile to the analysis and preserve unknown versus zero."""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def exports():
    from src.export_tableau import export_tableau
    export_tableau(ROOT)
    folder=ROOT/'exports/tableau'
    return {name:pd.read_csv(folder/f'{name}.csv') for name in ['school_season','brand_summary','switch_events']}

def test_full_panel_grain_missingness_and_percentile_definition(exports):
    x=exports['school_season']
    source=pd.read_csv(ROOT/'data/processed/analysis_panel.csv')
    assert len(x)==2833 and x.school.nunique()==358
    assert not x.duplicated(['school','season']).any()
    assert x.columns[:8].tolist()==['school','season','conference','brand','evidence_tier','rank','total_points','points_pctile']
    actual=x.sort_values(['school','season']).reset_index(drop=True)
    source=source.sort_values(['school','season']).reset_index(drop=True)
    assert np.allclose(actual.points_pctile,source.panel_points_pctile)
    assert actual.brand.fillna('').equals(source.brand.fillna(''))
    assert x.brand.isna().sum()==2296
    assert x.zero_imputed.sum()==438
    assert x.loc[x.zero_imputed,'rank'].isna().all()
    assert (x.loc[x.zero_imputed,'total_points']==0).all()
    assert x.conference.isna().sum()==436
    assert '2019-20' not in set(x.season)
    assert x.primary_included.sum()==537 and x.sensitivity_included.sum()==467

def test_every_brand_summary_reconciles_to_exported_rows(exports):
    panel=exports['school_season'];summary=exports['brand_summary']
    assert len(summary)==8 and not summary.duplicated(['evidence_tiers','brand']).any()
    for row in summary.itertuples():
        allowed=['A','B','C'] if row.evidence_tiers=='A+B+C' else ['A','B']
        g=panel[panel.in_research_scope & panel.evidence_tier.isin(allowed) & panel.brand.eq(row.brand)]
        assert len(g)==row.n_school_seasons
        assert g.school.nunique()==row.n_schools
        assert np.isclose(g.points_pctile.mean(),row.mean_points_pctile)
        assert np.isclose(g.points_pctile.median(),row.median_points_pctile)
        assert g['rank'].le(10).sum()==row.top10_finishes
        assert g['rank'].le(25).sum()==row.top25_finishes
        assert row.n_tier_A+row.n_tier_B+row.n_tier_C==len(g)

def test_switch_calendar_gaps_and_denver_are_not_disguised(exports):
    x=exports['switch_events']
    assert x.columns[:6].tolist()==['school','from_brand','to_brand','switch_season','relative_season','points_pctile']
    assert len(x)==50 and not x.duplicated(['school','switch_season','relative_season']).any()
    assert x.points_pctile.isna().sum()==12
    missing=x[x.school.eq('Washington')&x.relative_season.eq(0)].iloc[0]
    assert missing.season=='2019-20' and pd.isna(missing.points_pctile)
    assert not missing.outcome_available and not missing.primary_included
    denver=x[x.school.eq('Denver')&x.relative_season.lt(0)]
    assert denver.points_pctile.notna().all()
    assert denver.observed_brand.isna().all()
    assert not denver.primary_included.any() and not denver.usable_primary.any()
    assert x.primary_included.equals(x.sensitivity_included)
