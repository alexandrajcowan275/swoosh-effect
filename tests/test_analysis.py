"""Calendar lags and sample comparability are essential to the persistence test."""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import duckdb
from src.analyze import prepare_panel,fit_models

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def prepared():
    with duckdb.connect(str(ROOT/'data/processed/swoosh.duckdb'),read_only=True) as con:
        return prepare_panel(con.sql('SELECT * FROM analysis_panel').df())

def test_lag_is_calendar_year_not_previous_available_row(prepared):
    assert prepared.loc[prepared.year.isin([2017,2020]),'lag_points_pctile'].isna().all()
    for row in prepared[prepared.lag_points_pctile.notna()].itertuples():
        previous=prepared[(prepared.school_id==row.school_id)&(prepared.year==row.year-1)]
        assert len(previous)==1
        assert row.lag_points_pctile==previous.iloc[0].panel_points_pctile

def test_missing_conference_source_is_preserved(prepared):
    yale=prepared[(prepared.school=='Yale')&(prepared.season=='2020-21')].iloc[0]
    assert pd.isna(yale.conference) and yale.conference_model=='Ivy League'
    assert yale.zero_imputed and yale.total_points==0
    assert prepared[(prepared.school=='Yale')&(prepared.season=='2021-22')].iloc[0].lag_points_pctile==yale.panel_points_pctile

def test_matched_models_share_sample_and_inference_clusters(prepared):
    c,s,d=fit_models(prepared)
    for tiers,total,lag_n in [('A+B+C',537,401),('A+B',467,341)]:
        q=d[d.evidence_tiers==tiers].set_index('model')
        assert q.loc['plain','n']==total
        assert q.loc['plain_matched','n']==q.loc['lagged','n']==lag_n
        assert (q.cluster_df==q.n_schools-1).all()
        counts=s[s.evidence_tiers==tiers].pivot(index='brand',columns='model',values='n')
        assert counts.plain_matched.equals(counts.lagged)
    assert np.isfinite(c[['coefficient','ci_low','ci_high']]).all().all()
    assert (c.ci_low<=c.coefficient).all() and (c.ci_high>=c.coefficient).all()
    assert (s.loc[s.evidence_tiers=='A+B','n_C']==0).all()
