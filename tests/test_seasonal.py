"""Validate the expanded dataset without hiding publication inconsistencies."""
import hashlib
import json
from pathlib import Path
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def tables():
    out=ROOT/'data/processed'
    return (pd.read_csv(out/'sport_points_long.csv',low_memory=False),
            pd.read_csv(out/'seasonal_sport_observations.csv',low_memory=False),
            pd.read_csv(ROOT/'reports/period_reconciliation.csv'))


def test_every_season_has_all_sport_headers(tables):
    long, seasonal, _=tables
    assert len(long)==79234
    assert len(seasonal)==45704
    assert not long.duplicated(['season','school','sport']).any()
    for season,g in long.groupby('season'):
        assert set(g.period)=={'fall','winter','spring'}
        assert g.sport.nunique()==(40 if season=='2025-26' else 38)
    assert long.source_url.notna().all()
    assert long.source_page.ge(1).all()
    assert long.source_url_final.notna().all()
    assert long.sport_points.dropna().between(0,100).all()


def test_observed_source_sums_and_known_precision_differences(tables):
    _,seasonal,reconciliation=tables
    sums=seasonal.groupby(['season','school','period']).agg(
        sport_sum=('published_counted_points','sum'),
        printed_subtotal=('published_period_points','first'))
    assert (sums.sport_sum-sums.printed_subtotal).abs().max() <= .511
    # Do not silently round source numbers or discard the six 0.5 discrepancies.
    assert ((sums.sport_sum-sums.printed_subtotal).abs()>.11).sum()==6
    missing=reconciliation[reconciliation.status=='missing_period_row_nonzero_final_subtotal']
    assert set(zip(missing.season,missing.school,missing.period))=={
        ('2018-19','Seattle','fall'),('2020-21','SMU','fall'),
        ('2020-21','UAB','fall'),('2023-24','UC San Diego','winter')}
    assert missing.observed_sport_sum.isna().all()
    assert missing.final_period_points.gt(0).all()


def test_cannot_confuse_interim_scores_with_final_contributions(tables):
    long,_,_=tables
    interim=long[long.points_basis=='seasonal_publication']
    assert interim.excluded.isna().all()
    uncertain=interim[interim.status!='matches_final_subtotal']
    assert uncertain.counted_points.isna().all()
    assert long[long.points_basis=='final_publication'].counted_points.notna().all()
    # Actual first-page PDF evidence: Stanford's 2017 fall raw sum was 523,
    # while only 443 appears in the final PDF. Preserve both.
    stanford=interim[(interim.season=='2017-18')&(interim.school=='Stanford')&(interim.period=='fall')]
    assert stanford.sport_points.sum()==523
    assert stanford.counted_points.isna().all()
    assert stanford.set_index('sport').loc["Women's Cross Country",'sport_points']==80


def test_overflow_cells_are_auditable_derivations(tables):
    _,seasonal,_=tables
    overflow=seasonal[seasonal.source_value=='##']
    assert set(zip(overflow.season,overflow.school))=={
        ('2023-24','TCU'),('2024-25','West Virginia'),('2025-26','West Virginia')}
    assert overflow.sport.eq('Rifle').all()
    assert overflow.sport_points.eq(100).all()
    assert overflow.value_method.eq('derived_from_published_subtotal_single_overflow_cell').all()


def test_source_checksums():
    manifest=json.loads((ROOT/'data/seasonal_sources.json').read_text())
    assert len(manifest)==16
    for s in manifest:
        assert hashlib.sha256((ROOT/s['file']).read_bytes()).hexdigest()==s['sha256']


def test_new_winter_sports_match_visually_reviewed_header(tables):
    _,seasonal,_=tables
    row=seasonal[(seasonal.season=='2025-26')&(seasonal.school=='Stanford')&(seasonal.period=='winter')].set_index('sport')
    assert row.loc["Women's Fencing",'sport_points']==60
    assert row.loc["Men's Fencing",'sport_points']==45
    assert row.loc["Women's Wrestling",'sport_points']==0
    assert row.loc["Men's Wrestling",'sport_points']==73.5
