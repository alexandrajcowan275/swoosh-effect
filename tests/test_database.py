"""Guard against dropped schools, guessed sponsors, and false brand switches."""
from pathlib import Path
import duckdb
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def db():
    # Build from committed inputs so the ignored database is not a prerequisite.
    from src import build_database as module
    module.build()
    with duckdb.connect(str(ROOT/'data/processed/swoosh.duckdb'),read_only=True) as con:
        yield con

def test_panel_preserves_official_totals_and_every_name(db):
    raw=pd.read_csv(ROOT/'data/processed/standings.csv')
    mapping=pd.read_csv(ROOT/'data/school_name_map.csv')
    assert set(raw.school)==set(mapping.school_raw)
    panel=db.sql('SELECT * FROM standings').df()
    matched=raw.merge(panel[panel.observed_in_final],left_on=['school','season'],right_on=['school_raw','season'],suffixes=('_raw','_panel'),validate='one_to_one')
    assert len(matched)==len(raw)
    assert (matched.total_points_raw==matched.total_points_panel).all()
    assert len(panel)==8*db.sql('SELECT count(*) FROM schools').fetchone()[0]-31
    assert not panel.duplicated(['school_id','season']).any()

def test_zeros_cannot_masquerade_as_verified_eligibility(db):
    missing=db.sql('SELECT * FROM standings WHERE zero_imputed').df()
    assert len(missing)>0
    assert (missing.total_points==0).all()
    assert missing.conference.isna().all()
    assert missing.source_url.isna().all()
    assert (missing.eligibility_status=='kept_known_d1_program').all()
    audit=pd.read_csv(ROOT/'reports/zero_row_audit.csv')
    assert len(audit)==469 and audit.keep.sum()==438
    assert not ((missing.school=='Hartford') & (missing.season>'2022-23')).any()
    assert not ((missing.school=='St. Thomas') & (missing.season<'2021-22')).any()

def test_unknown_sponsors_not_assigned_or_modeled(db):
    unknown=db.sql("SELECT * FROM sponsor_coverage WHERE evidence_tier='unknown'").df()
    assert len(unknown)>0 and unknown.brand.isna().all()
    assert db.sql("SELECT count(*) FROM verified_observed_panel WHERE sponsor_verified<>'Y' OR NOT observed_in_final").fetchone()[0]==0
    assert db.sql("SELECT count(*) FROM sponsor_seasons WHERE source_url IS NULL OR brand IS NULL").fetchone()[0]==0

def test_priority_scope_includes_every_top50_school(db):
    missing=db.sql('SELECT DISTINCT school_id FROM standings WHERE rank<=50 EXCEPT SELECT school_id FROM sponsor_scope').df()
    assert missing.empty
    assert db.sql('SELECT count(*) FROM sponsor_scope').fetchone()[0]==74

def test_switches_use_effective_season(db):
    actual=db.sql("SELECT season,previous_brand,brand FROM brand_switches WHERE school='Auburn'").fetchall()
    assert actual==[('2025-26','Under Armour','Nike')]
    # No Nike/Jordan change and no gaps may become a switch.
    sql=(ROOT/'sql/analysis_views.sql').read_text().split('CREATE OR REPLACE VIEW brand_switches AS')[1]
    with duckdb.connect() as mem:
        mem.execute('CREATE TABLE sponsor_coverage(school_id VARCHAR,school VARCHAR,season VARCHAR,brand VARCHAR,source_url VARCHAR,verified VARCHAR)')
        mem.executemany('INSERT INTO sponsor_coverage VALUES (?,?,?,?,?,?)',[
            ('gap','Gap','2018-19','adidas','a','Y'),('gap','Gap','2020-21','Nike','b','Y'),
            ('same','Same','2024-25','Nike','a','Y'),('same','Same','2025-26','Nike','b','Y'),
            ('real','Real','2024-25','adidas','a','Y'),('real','Real','2025-26','Nike','b','Y')])
        assert mem.sql(sql).df().school.tolist()==['Real']

def test_review_accounts_for_every_unknown(db):
    review=pd.read_csv(ROOT/'reports/sponsor_research_review.csv').fillna('')
    coverage=db.sql('SELECT * FROM sponsor_coverage WHERE in_research_scope').df()
    assert set(review.school)==set(coverage.school)
    for row in review.itertuples():
        unknown=coverage[(coverage.school==row.school)&(coverage.evidence_tier=='unknown')].season.tolist()
        assert row.missing_seasons==', '.join(unknown)
        assert row.covered_seasons==8-len(unknown)
        assert row.verified_seasons==row.tier_A+row.tier_B
        if unknown:
            assert row.required_followup and row.research_status!='reviewed_full_coverage'
    scope=db.sql('SELECT school,research_status FROM sponsor_scope').df()
    assert scope.set_index('school').research_status.to_dict()==review.set_index('school').research_status.to_dict()

def test_conflicting_and_excluded_seasons_are_not_backfilled(db):
    assert db.sql("SELECT season FROM sponsor_coverage WHERE school='Iowa State' AND verified='Y'").fetchall()==[('2017-18',)]
    events=pd.read_csv(ROOT/'reports/sponsor_switch_events.csv')
    assert events[events.school=='Washington'].season.tolist()==['2019-20']
    assert db.sql("SELECT count(*) FROM brand_switches WHERE school='Washington'").fetchone()[0]==0
    assert db.sql("SELECT count(*) FROM standings WHERE season='2019-20'").fetchone()[0]==0
