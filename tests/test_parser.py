"""Regression checks against real PDFs and visually reviewed first-page fixtures."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from parse_standings import parse_pdf


@pytest.fixture(scope='module')
def actual():
    return pd.read_csv(ROOT/'data/processed/standings.csv'), pd.read_csv(ROOT/'data/processed/spring_sport_points.csv')


def test_top_five_against_visual_transcription(actual):
    schools, _ = actual
    expected = json.loads((ROOT/'tests/fixtures/top5.json').read_text())
    for season, rows in expected.items():
        observed = schools[schools.season == season].head(5)
        assert observed[['school','total_points']].values.tolist() == rows
        assert observed['rank'].tolist() == [1,2,3,4,5]


def test_complete_rows_and_ranks(actual):
    schools, sports = actual
    assert schools.season.nunique() == 8
    assert '2019-20' not in set(schools.season)
    assert not schools.duplicated(['season','school']).any()
    assert not sports.duplicated(['season','school','sport']).any()
    assert (sports.groupby(['season','school']).size() == 14).all()
    for _, group in schools.groupby('season'):
        assert group['rank'].tolist() == group.total_points.rank(method='min', ascending=False).astype(int).tolist()
        assert group.points_pctile.tolist() == pytest.approx(group.total_points.rank(method='average',pct=True)*100)


def test_excluded_values_not_fabricated(actual):
    _, sports = actual
    excluded = sports[sports.excluded]
    assert len(excluded) > 0
    assert excluded.sport_points.isna().all()
    assert (excluded.counted_points == 0).all()
    assert (excluded.source_value.str.lower() == 'x').all()
    assert sports.source_url.notna().all()
    assert sports.source_page.ge(1).all()


def test_real_pdf_parser_and_realignments(actual):
    # Real institution realignments remain checked against the audited tables.
    season = actual[0][actual[0].season == '2024-25'].set_index('school')
    assert season.loc['USC', 'conference'] == 'Big Ten'
    assert season.loc['Stanford', 'conference'] == 'ACC'
    source = json.loads((ROOT/'tests/fixtures/pdf_manifest.json').read_text())[0]
    schools, sports = parse_pdf(ROOT/source['file'], source['season'], source['source_url'])
    assert schools.school.tolist() == ['Example State', 'Example College']
    assert schools.conference.tolist() == ['Example East', 'Example West']
    assert schools.total_points.tolist() == [150, 75]
    assert schools.spring_points.tolist() == [100, 25]
    assert len(sports) == 28
    row = sports[(sports.school=='Example State') & (sports.sport=="Women's Rowing")].iloc[0]
    assert row.sport_points == 100 and row.source_page == 1
    excluded = sports[sports.excluded]
    assert len(excluded) == 1 and excluded.sport_points.isna().all()
    assert excluded.counted_points.eq(0).all()


def test_published_subtotal_reconciliation(actual):
    schools, sports = actual
    spring = sports.groupby(['season','school']).counted_points.sum()
    indexed = schools.set_index(['season','school'])
    assert indexed.spring_points.sort_index().tolist() == pytest.approx(spring.sort_index().tolist(), abs=0.01)
    assert schools.total_points.tolist() == pytest.approx(schools[['spring_points','winter_points','fall_points']].sum(axis=1).tolist(), abs=0.01)
    cleveland = schools[(schools.season=='2021-22') & (schools.school=='Cleveland State')].iloc[0]
    assert cleveland.conference == 'Horizon League'
    assert cleveland.division == 'DI'


def test_visually_reviewed_name_conference_boundaries(actual):
    schools, sports = actual
    assert schools[['school', 'conference']].notna().all().all()
    for season, points in [('2017-18', 8.6), ('2018-19', 122.6)]:
        row = schools[(schools.season == season) & (schools.school == "St. Mary's College of California")].iloc[0]
        assert row.conference == 'WCC'
        assert row.total_points == points
    row = schools[(schools.season == '2022-23') & (schools.school == 'Merrimack')].iloc[0]
    assert row.conference == 'Northeast (Fall 2023)'
    assert row.total_points == 25
    assert not schools.school.str.contains('CaliforniaWCC|Merrimack Northeast').any()
    assert not sports.school.str.contains('CaliforniaWCC|Merrimack Northeast').any()
