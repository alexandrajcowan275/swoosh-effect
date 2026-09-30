"""Boundary tests for continuity: no extrapolation, switch crossing, or false certainty."""
import pandas as pd
from src.evidence_tiers import assign_continuity


def history():
    seasons=['2017-18','2018-19','2020-21','2021-22','2022-23','2023-24']
    return pd.DataFrame([dict(school='Example',season=s,brand='Nike' if i in (1,4) else None,
        brand_raw='Nike' if i in (1,4) else None,evidence_tier='A' if i==1 else 'B' if i==4 else None,
        verified='Y' if i in (1,4) else 'N',source_url=f'https://example.edu/{s}' if i in (1,4) else None,
        in_research_scope=True) for i,s in enumerate(seasons)])


def test_bounded_continuity_never_extrapolates_or_cascades():
    x=assign_continuity(history(),[])
    assert x.evidence_tier.tolist()==['unknown','A','C','C','B','unknown']
    assert x[x.inferred].left_anchor_season.unique().tolist()==['2018-19']
    assert x[x.inferred].right_anchor_season.unique().tolist()==['2022-23']
    assert (x[x.inferred].verified=='N').all()


def test_known_switch_even_with_same_endpoints_blocks_continuity():
    x=assign_continuity(history(),[{'school':'Example','transition_date':'2020-07-01'}])
    assert x.evidence_tier.eq('C').sum()==0


def test_different_brands_and_outside_scope_are_not_inferred():
    h=history();h.loc[4,'brand']='adidas'
    assert not assign_continuity(h,[]).inferred.any()
    h=history();h['in_research_scope']=False
    assert not assign_continuity(h,[]).inferred.any()


def test_primary_and_sensitivity_samples_are_explicit():
    from pathlib import Path
    x=pd.read_csv(Path(__file__).resolve().parents[1]/'reports/sponsor_coverage.csv')
    x=x[x.in_research_scope]
    assert x.evidence_tier.value_counts().to_dict()=={'A':445,'C':70,'unknown':55,'B':22}
    assert x[x.evidence_tier=='unknown'].brand.isna().all()
    inferred=x[x.evidence_tier=='C']
    assert not inferred.season.isin(['2017-18','2025-26']).any()
    assert inferred[['left_anchor_url','right_anchor_url']].notna().all().all()
