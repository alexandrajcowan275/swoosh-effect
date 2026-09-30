"""Join sourced fall/winter/spring observations; expose every unresolved difference.

Annual rank, conference and total always come from the final PDF. Interim
points are not silently treated as year-end contributions or overwritten.
"""
import json
import pandas as pd
from parse_standings import ROOT

KEYS = ['season','school']

def main():
    out = ROOT/'data/processed'
    final = pd.read_csv(out/'standings.csv')
    spring = pd.read_csv(out/'spring_sport_points.csv')
    seasonal = pd.read_csv(out/'seasonal_sport_observations.csv', low_memory=False)
    summaries = pd.read_csv(out/'seasonal_standings.csv')
    sources = json.loads((ROOT/'data/seasonal_sources.json').read_text())
    source_map = {(s['season'],s['period']):s['source_url'] for s in sources}
    reports = []
    for period in ['fall','winter']:
        sums = seasonal[seasonal.period==period].groupby(KEYS).published_counted_points.sum().rename('observed_sport_sum')
        joined = final.merge(summaries[summaries.period==period][KEYS+['published_period_points','source_url','source_page']],on=KEYS,how='left',suffixes=('_final','_seasonal')).merge(sums,on=KEYS,how='left')
        for row in joined.to_dict('records'):
            target = row[period+'_points']
            observed = row['observed_sport_sum']
            if pd.isna(observed):
                status = 'no_period_row_zero_final_subtotal' if target == 0 else 'missing_period_row_nonzero_final_subtotal'
            elif abs(observed-target) <= 0.011:
                status = 'matches_final_subtotal'
            elif abs(observed-target) <= 0.511:
                status = 'small_published_precision_or_source_difference'
            elif observed > target:
                status = 'year_end_reduction_requires_exclusion_detail'
            else:
                status = 'final_exceeds_observed_requires_updated_source'
            reports.append(dict(season=row['season'],school=row['school'],period=period,
                                observed_sport_sum=observed,published_period_points=row['published_period_points'],
                                final_period_points=target,
                                final_minus_observed=None if pd.isna(observed) else round(target-observed,6),
                                publication_sum_difference=None if pd.isna(observed) else round(observed-row['published_period_points'],6),
                                status=status,seasonal_source_url=source_map[(row['season'],period)],
                                seasonal_source_page=row['source_page_seasonal'],
                                final_source_url=row['source_url_final'],final_source_page=row['source_page_final']))
    reconciliation = pd.DataFrame(reports)
    reconciliation.to_csv(ROOT/'reports/period_reconciliation.csv',index=False)
    unresolved = reconciliation[reconciliation.status.isin(['missing_period_row_nonzero_final_subtotal','final_exceeds_observed_requires_updated_source'])]
    unresolved.to_csv(ROOT/'reports/source_discrepancies.csv',index=False)

    # Enrich interim observations with FINAL conference/rank/total/percentile.
    seasonal = seasonal.merge(final[KEYS+['conference','rank','total_points','points_pctile','source_url','source_page']],on=KEYS,validate='many_to_one',suffixes=('','_final'))
    seasonal = seasonal.merge(reconciliation[KEYS+['period','status']],on=KEYS+['period'],validate='many_to_one')
    seasonal['points_basis'] = 'seasonal_publication'
    seasonal['counted_points'] = seasonal.published_counted_points.where(seasonal.status=='matches_final_subtotal')
    seasonal['counted_points_basis'] = seasonal.status.map(lambda s: 'subtotal_consistent_not_individually_reverified' if s=='matches_final_subtotal' else 'unknown_at_year_end')
    seasonal['excluded'] = pd.NA  # No year-end exclusion flag is supplied by these interim PDFs.
    spring['period'] = 'spring'
    spring['points_basis'] = 'final_publication'
    spring['value_method'] = 'printed'
    spring['published_counted_points'] = spring.counted_points
    spring['excluded_at_publication'] = spring.excluded
    spring['counted_points_basis'] = 'printed_final'
    spring['status'] = 'matches_final_subtotal'
    spring['source_url_final'] = spring.source_url
    spring['source_page_final'] = spring.source_page
    combined = pd.concat([spring,seasonal],ignore_index=True)
    columns = ['season','school','conference','rank','total_points','sport','sport_points','points_pctile',
               'period','points_basis','source_value','source_place','sport_place','excluded_at_publication',
               'published_counted_points','counted_points','counted_points_basis','excluded','value_method','status',
               'source_url','source_page','source_url_final','source_page_final']
    combined[columns].to_csv(out/'sport_points_long.csv',index=False)
    counts=combined.groupby(['season','period']).size().unstack(fill_value=0)
    report=dict(school_seasons=len(final),sport_observations=len(combined),seasonal_observations=len(seasonal),
                source_documents=24,source_overflow_cells_derived=int(seasonal.value_method.ne('printed').sum()),
                status_counts=reconciliation.status.value_counts().to_dict(),
                missing_or_increased_school_periods=len(unresolved),
                year_end_contribution_uncertain_school_periods=int((~reconciliation.status.isin(['matches_final_subtotal','no_period_row_zero_final_subtotal'])).sum()),
                complete_year_end_sport_breakdown=False,
                note='All available seasonal sport rows extracted. Source omissions and revisions remain explicit; no missing sport scores are fabricated.')
    (ROOT/'reports/coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(counts.to_string());print(json.dumps(report,indent=2))

if __name__=='__main__': main()
