"""Audit absent final-standings rows against reviewed Division I program intervals."""
import pandas as pd


def audit_zeros(standings, reviews):
    zeros = standings[standings.zero_imputed].copy()
    assert reviews.school.is_unique
    assert set(zeros.school) == set(reviews.school), 'Every imputed program needs review'
    zeros = zeros.merge(reviews, on='school', validate='many_to_one')
    zeros['keep'] = (zeros.season >= zeros.first_d1_season) & (zeros.season <= zeros.last_d1_season)
    zeros['disposition'] = zeros.keep.map({True:'kept_known_d1_program', False:'dropped_outside_d1_program_interval'})
    panel = standings.merge(zeros[['school_id','season','keep','disposition']], on=['school_id','season'], how='left', validate='one_to_one')
    panel = panel[panel.observed_in_final | panel.keep.eq(True)].copy()
    panel['eligibility_status'] = panel.disposition.fillna('observed_scoring_school')
    panel = panel.drop(columns=['keep','disposition'])
    # Fixed observed-ever universe, eligible years only; not a census of all D1 schools.
    panel['panel_points_pctile'] = panel.groupby('season').total_points.rank(pct=True)*100
    return panel, zeros
