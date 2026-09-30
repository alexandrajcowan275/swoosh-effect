"""Compare actual rebuilt assignments to the frozen pre-refactor Phase 3 output."""
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'tests/fixtures'


def assert_identical(actual,baseline,keys,label):
    expected=pd.read_csv(FIXTURES/baseline).fillna('')
    actual=actual[expected.columns].fillna('')
    expected=expected.sort_values(keys).reset_index(drop=True).astype(str)
    actual=actual.sort_values(keys).reset_index(drop=True).astype(str)
    if not expected.equals(actual):
        before,after=expected.set_index(keys).align(actual.set_index(keys),join='outer')
        differences=before.fillna('<absent>').compare(after.fillna('<absent>'),result_names=('before','after'))
        path=ROOT/'reports/algorithm_regression_diff.csv'
        differences.to_csv(path)
        raise AssertionError(f'{label} changed after refactor. STOP: inspect {path}.\n{differences.to_string()}')


def test_frozen_baseline_has_not_changed():
    meta=json.loads((FIXTURES/'phase3_baseline.json').read_text())
    assert meta['baseline_id']=='phase3-pre-algorithm-refactor'
    for name,checksum in meta['files'].items():
        assert hashlib.sha256((FIXTURES/name).read_bytes()).hexdigest()==checksum


def test_pipeline_assignments_and_names_identical_to_phase3():
    from src.build_database import build
    build()
    assert_identical(pd.read_csv(ROOT/'reports/sponsor_coverage.csv'),'phase3_sponsor_assignments.csv',['school_id','season'],'Sponsor assignments')
    assert_identical(pd.read_csv(ROOT/'reports/name_match_audit.csv'),'phase3_name_matches.csv',['school_raw'],'Name matches')
    review=pd.read_csv(ROOT/'reports/name_manual_review.csv')
    assert review.empty


def test_model_results_identical_after_refactor():
    import duckdb
    from src.analyze import prepare_panel,fit_models
    with duckdb.connect(str(ROOT/'data/processed/swoosh.duckdb'),read_only=True) as con:
        coefficients,_,_=fit_models(prepare_panel(con.sql('SELECT * FROM analysis_panel').df()))
    expected=pd.read_csv(FIXTURES/'phase3_model_coefficients.csv')
    # Formula fits are deterministic here; tight numeric tolerance allows CSV
    # round-trip rounding without permitting material coefficient changes.
    keys=['evidence_tiers','model','term']
    pd.testing.assert_frame_equal(coefficients.sort_values(keys).reset_index(drop=True).fillna(''),
        expected.sort_values(keys).reset_index(drop=True).fillna(''),check_exact=False,rtol=1e-12,atol=1e-12)
