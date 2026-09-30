"""Build a sourced department-level panel; unknown sponsors stay unknown."""
import json
from pathlib import Path
import duckdb
import pandas as pd
if __package__:
    from .research_report import write_research_report
    from .evidence_tiers import expand_evidence, assign_continuity
    from .membership import audit_zeros
    from .name_matching import resolve_school_names
else:
    from research_report import write_research_report
    from evidence_tiers import expand_evidence, assign_continuity
    from membership import audit_zeros
    from name_matching import resolve_school_names

ROOT = Path(__file__).resolve().parents[1]

def build():
    mapping = pd.read_csv(ROOT/'data/school_name_map.csv')
    source = pd.read_csv(ROOT/'data/processed/standings.csv').rename(columns={'school':'school_raw'})
    sports = pd.read_csv(ROOT/'data/processed/sport_points_long.csv',low_memory=False).rename(columns={'school':'school_raw'})
    assert mapping.school_raw.is_unique
    matches,manual=resolve_school_names(set(source.school_raw)|set(sports.school_raw),mapping.to_dict('records'),threshold=2)
    match_table=pd.DataFrame(matches,columns=['school_raw','school','school_id','match_method','edit_distance'])
    match_table.to_csv(ROOT/'reports/name_match_audit.csv',index=False)
    pd.DataFrame(manual,columns=['school_raw','closest_distance','threshold','candidate_schools','candidate_ids','reason']).to_csv(ROOT/'reports/name_manual_review.csv',index=False)
    if manual:
        raise ValueError('School names require manual review; see reports/name_manual_review.csv. No unmatched rows were dropped.')
    observed = source.merge(match_table[['school_raw','school','school_id']], on='school_raw', validate='many_to_one')
    assert not observed.duplicated(['school_id','season']).any()
    schools = mapping[['school_id','school']].drop_duplicates()
    assert schools.school_id.is_unique
    seasons = sorted(source.season.unique())
    grid = pd.MultiIndex.from_product([schools.school_id, seasons], names=['school_id','season']).to_frame(index=False)
    standings = grid.merge(observed.drop(columns='school'), on=['school_id','season'], how='left', validate='one_to_one').merge(schools,on='school_id',validate='many_to_one')
    standings['observed_in_final'] = standings.source_url.notna()
    standings['zero_imputed'] = ~standings.observed_in_final
    standings['total_points'] = standings.total_points.fillna(0)
    standings, zero_audit = audit_zeros(standings, pd.read_csv(ROOT/'data/division_i_membership_review.csv'))
    zero_audit.to_csv(ROOT/'reports/zero_row_audit.csv',index=False)
    sports = sports.merge(match_table[['school_raw','school_id']],on='school_raw',validate='many_to_one')
    assert sports.school_id.notna().all()
    evidence = pd.DataFrame(json.loads((ROOT/'data/sponsor_evidence.json').read_text()))
    sponsors = evidence.merge(schools,on='school',validate='many_to_one')
    assert sponsors.school_id.notna().all()
    sponsor_seasons = expand_evidence(evidence, schools, seasons)
    scope = pd.read_csv(ROOT/'data/sponsor_scope.csv').merge(schools,on='school',validate='one_to_one')
    fields=['school_id','season','brand','brand_raw','source_url','verified','evidence_summary','verification_basis','evidence_tier','evidence_id','source_type','source_date','archive_url','snapshot_date']
    coverage = grid.merge(schools,on='school_id').merge(sponsor_seasons[fields],on=['school_id','season'],how='left')
    coverage['verified'] = coverage.verified.fillna('N')
    coverage['in_research_scope'] = coverage.school_id.isin(scope.school_id)
    transitions=json.loads((ROOT/'data/sponsor_transition_register.json').read_text())
    coverage,brand_periods,gap_audit=assign_continuity(coverage,transitions,return_audit=True)
    brand_periods.to_csv(ROOT/'reports/sponsor_brand_periods.csv',index=False)
    gap_audit.to_csv(ROOT/'reports/sponsor_gap_audit.csv',index=False)
    sponsor_seasons=coverage[coverage.covered].copy()
    scope['research_status']=scope.school.map(coverage[coverage.in_research_scope].groupby('school').covered.all()).map({True:'reviewed_full_coverage',False:'reviewed_partial_coverage'})
    out = ROOT/'data/processed'
    sponsors.to_csv(out/'sponsors.csv',index=False)
    sponsor_seasons.to_csv(out/'sponsor_seasons.csv',index=False)
    coverage.to_csv(ROOT/'reports/sponsor_coverage.csv',index=False)
    standings.to_csv(out/'school_season_panel.csv',index=False)
    with duckdb.connect(str(out/'swoosh.duckdb')) as con:
        for name, frame in [('schools',schools),('standings',standings),('sport_points',sports),('sponsors',sponsors),('sponsor_seasons',sponsor_seasons),('sponsor_coverage',coverage),('sponsor_scope',scope)]:
            con.register('_input',frame)
            con.execute(f'CREATE OR REPLACE TABLE {name} AS SELECT * FROM _input')
            con.unregister('_input')
        con.execute((ROOT/'sql/analysis_views.sql').read_text())
        switches=con.sql('SELECT * FROM brand_switches ORDER BY school, season').df()
        switches.to_csv(ROOT/'reports/brand_switches.csv',index=False)
    priority = coverage[coverage.in_research_scope]
    counts=priority.evidence_tier.value_counts().to_dict()
    report = dict(canonical_schools=len(schools),mapped_source_names=len(mapping),observed_school_seasons=len(observed),panel_rows=len(standings),zero_rows_reviewed=len(zero_audit),zero_rows_kept=int(zero_audit.keep.sum()),zero_rows_dropped=int((~zero_audit.keep).sum()),priority_schools=len(scope),priority_school_seasons=len(priority),evidence_tier_counts=counts,covered_priority_school_seasons=int(priority.covered.sum()),coverage_percent=round(100*priority.covered.mean(),2),direct_priority_school_seasons=int(priority.evidence_tier.isin(['A','B']).sum()),fully_covered_priority_schools=int(priority.groupby('school').covered.all().sum()),unknown_priority_school_seasons=int(priority.evidence_tier.eq('unknown').sum()),verified_brand_switches=len(switches),status='90% evidence threshold reached; evidence audit complete; run.sh rebuilds the analysis outputs')
    write_research_report(ROOT, priority, evidence, switches, report)
    (ROOT/'reports/database_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    build()
