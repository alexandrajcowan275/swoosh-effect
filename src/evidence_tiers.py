"""Assign direct evidence first; infer only bounded, transition-free gaps."""
import pandas as pd
if __package__:
    from .algorithms import merge_intervals
else:
    from algorithms import merge_intervals


def expand_evidence(evidence, schools, seasons):
    rows=[]
    ids=schools.set_index('school').school_id.to_dict()
    assert evidence.evidence_id.is_unique
    for row in evidence.to_dict('records'):
        assert row['evidence_tier'] in ('A','B')
        if row['evidence_tier']=='B':
            assert row['start_season']==row['end_season'], 'B is a dated season snapshot'
            date=row.get('snapshot_date') or row.get('source_date')
            assert date and pd.notna(date), 'B needs an actual source or snapshot date'
            year=int(row['start_season'][:4])
            assert f'{year}-07-01'<=date<=f'{year+1}-06-30'
        for season in seasons:
            if row['start_season']<=season<=row['end_season']:
                rows.append({**row,'school_id':ids[row['school']],'season':season})
    result=pd.DataFrame(rows)
    # Multiple corroborating sources are allowed; conflicting brand identities require resolution.
    assert result.groupby(['school','season']).brand.nunique().max()==1, 'Conflicting provider evidence'
    return result.sort_values(['school','season','evidence_tier','evidence_id']).drop_duplicates(['school_id','season'])


def assign_continuity(coverage, transitions, return_audit=False):
    result=coverage.copy()
    result['evidence_tier']=result.evidence_tier.fillna('unknown')
    for col in ['left_anchor_season','right_anchor_season','left_anchor_url','right_anchor_url']:
        result[col]=None
    result['inferred']=False
    periods=[];gaps=[]
    # Hand-written interval merging and bounded-gap inference owns this logic.
    direct=result[result.evidence_tier.isin(['A','B'])]
    for school,history in result[result.in_research_scope].groupby('school'):
        anchors=direct[direct.school.eq(school)].sort_values('season').to_dict('records')
        intervals=[{**a,'start_season':a['season'],'end_season':a['season']} for a in anchors]
        merged=merge_intervals(intervals,seasons=history.season.tolist(),
            transitions=[e['transition_date'] for e in transitions if e['school']==school])
        for p in merged['periods']:
            periods.append({'school':school,**p,'covered_seasons':', '.join(p['covered_seasons'])})
        for gap in merged['gaps']:
            left,right=gap['left_anchor'],gap['right_anchor']
            gaps.append(dict(school=school,start_season=gap['start_season'],end_season=gap['end_season'],
                candidate_seasons=', '.join(gap['seasons']),inferred=gap['inferred'],reason=gap['reason'],
                left_anchor_season=left['season'] if left else None,right_anchor_season=right['season'] if right else None,
                left_anchor_url=left['source_url'] if left else None,right_anchor_url=right['source_url'] if right else None))
        indices=dict(zip(history.season,history.index))
        for assignment in merged['inferred']:
            index=indices[assignment['season']]
            left,right=assignment['left_anchor'],assignment['right_anchor']
            result.loc[index,['brand','brand_raw','evidence_tier','inferred','verified']]=[left['brand'],left['brand_raw'],'C',True,'N']
            result.loc[index,['left_anchor_season','right_anchor_season','left_anchor_url','right_anchor_url']]=[left['season'],right['season'],left['source_url'],right['source_url']]
            result.loc[index,'source_url']=left['source_url']
            result.loc[index,'evidence_summary']=f"Inferred between {left['season']} ({left['evidence_tier']}) and {right['season']} ({right['evidence_tier']}); same provider and no known intervening transition in reviewed evidence."
            result.loc[index,'verification_basis']='continuity inference; endpoints only, not direct seasonal observation'
            result.loc[index,'source_type']='inferred_from_two_sources'
    result['covered']=result.evidence_tier.isin(['A','B','C'])
    result['research_status']=result.evidence_tier.map({'A':'direct_contract_evidence','B':'dated_official_use','C':'inferred_continuity','unknown':'unknown'})
    result.loc[~result.in_research_scope,'research_status']='outside_priority_scope'
    if return_audit:
        return result,pd.DataFrame(periods),pd.DataFrame(gaps)
    return result
