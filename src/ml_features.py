"""Pre-season features with exact calendar joins and auditable brand masking.

No target-season scores, ranks, sport totals, or conference observations enter X.
Brand is the department assignment only when its direct evidence is dated before
August 1 of the target year; Tier C and undated/late evidence are never predictors.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
META = ['school_id', 'school', 'season', 'year', 'points_pctile', 'cutoff_date',
        'lag1_source_year', 'lag2_source_year', 'brand_evidence_tier',
        'brand_source_date', 'brand_date_basis', 'brand_source_url', 'brand_status']


def evidence_date(record):
    """Return a conservative observed date and its provenance; never guess a year.

    An explicit source_date takes precedence over a full date embedded in a URL.
    An archive snapshot can only move availability later. URL-derived dates are
    proxies for publication, not a claim that every historical page was archived.
    """
    value = str(record.get('source_date', ''))
    basis = 'explicit_source_date'
    if not re.match(r'^\d{4}-\d{2}-\d{2}(?:$|T| )', value):
        match = re.search(r'/((?:19|20)\d{2})/(\d{1,2})/(\d{1,2})(?:/|$)',
                          str(record.get('source_url', '')))
        if not match:
            return None, 'undated'
        value = f'{match[1]}-{int(match[2]):02d}-{int(match[3]):02d}'
        basis = 'date_in_source_url'
    try:
        dated = datetime.strptime(value[:10], '%Y-%m-%d').date()
        snapshot = str(record.get('snapshot_date', ''))
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', snapshot):
            observed = datetime.strptime(snapshot, '%Y-%m-%d').date()
            if observed > dated:
                dated, basis = observed, 'archive_snapshot_date'
    except ValueError:
        return None, 'invalid_date'
    return dated, basis


def build_features(panel, sports, mapping, sponsors):
    """Assemble X and y separately by exact school/calendar year.

    Sport inputs are prior-season published per-sport points, not reconstructed
    annual counted contributions. Null/absent scores stay null. A sport vocabulary
    fixed from the earliest source season avoids discovering features in holdout.
    """
    panel = panel.copy()
    panel['year'] = panel.season.str[:4].astype(int)
    if panel.duplicated(['school_id', 'year']).any():
        raise ValueError('Duplicate school-season targets')
    out = panel[['school_id', 'school', 'season', 'year', 'panel_points_pctile']].rename(
        columns={'panel_points_pctile': 'points_pctile'})
    out['cutoff_date'] = out.year.astype(str) + '-08-01'
    out['season_year'] = out.year - 2017
    for lag in (1, 2):
        cols = ['school_id', 'year', 'panel_points_pctile']
        if lag == 1:
            cols.append('conference')
        prior = panel[cols].copy()
        prior[f'lag{lag}_source_year'] = prior.year
        prior['year'] += lag
        prior = prior.rename(columns={'panel_points_pctile': f'points_pctile_lag{lag}',
                                      'conference': 'conference_prior'})
        out = out.merge(prior, on=['school_id', 'year'], how='left', validate='one_to_one')
    out['conference_prior'] = out.conference_prior.replace({'Pac 12': 'Pac-12'}).fillna('Unknown')

    evidence = sponsors.set_index(['school_id', 'season']).to_dict('index')
    for row in out.itertuples():
        source = evidence.get((row.school_id, row.season), {})
        date, basis = evidence_date(source)
        tier = source.get('evidence_tier', 'unknown')
        eligible = tier in {'A', 'B'} and date is not None and str(date) < row.cutoff_date
        status = ('eligible_direct_preseason' if eligible else
                  'continuity_excluded' if tier == 'C' else
                  'no_direct_evidence' if tier not in {'A', 'B'} else
                  'undated_or_invalid' if date is None else 'published_after_cutoff')
        values = dict(brand=source.get('brand') if eligible else 'Unknown',
                      brand_evidence_tier=tier if eligible else 'unknown',
                      brand_source_date=str(date) if date else '', brand_date_basis=basis,
                      brand_source_url=source.get('source_url', ''), brand_status=status)
        for key, value in values.items():
            out.loc[row.Index, key] = value

    sports = sports.copy()
    sports['year'] = sports.season.str[:4].astype(int)
    vocabulary = sorted(sports.loc[sports.year.eq(sports.year.min()), 'sport'].unique())
    name_map = mapping[['school_raw', 'school_id']].drop_duplicates()
    sports = sports.merge(name_map, left_on='school', right_on='school_raw',
                          how='left', validate='many_to_one')
    if sports.school_id.isna().any():
        raise ValueError('Unmapped school in sport features')
    if sports.duplicated(['school_id', 'year', 'sport']).any():
        raise ValueError('Duplicate sport observation')
    wide = sports.pivot(index=['school_id', 'year'], columns='sport', values='sport_points')
    wide = wide.reindex(columns=vocabulary)
    wide.columns = ['sport_lag1__' + re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
                    for name in vocabulary]
    wide = wide.reset_index()
    wide['year'] += 1
    out = out.merge(wide, on=['school_id', 'year'], how='left', validate='one_to_one')
    return out.sort_values(['year', 'school_id']).reset_index(drop=True)


def load_features(root=ROOT):
    return build_features(pd.read_csv(root/'data/processed/analysis_panel.csv'),
                          pd.read_csv(root/'data/processed/sport_points_long.csv', low_memory=False),
                          pd.read_csv(root/'data/school_name_map.csv'),
                          pd.read_csv(root/'data/processed/sponsor_seasons.csv'))


def feature_columns(frame, *, ols=False, brand=True):
    numeric = ['points_pctile_lag1', 'season_year']
    if not ols:
        numeric += ['points_pctile_lag2'] + sorted(c for c in frame if c.startswith('sport_lag1__'))
    categorical = ['conference_prior'] + (['brand'] if brand else [])
    return numeric, categorical


def temporal_split(frame):
    """Reserve the most recent two whole seasons before selecting model settings."""
    years = sorted(frame.year.unique())
    if len(years) < 5:
        raise ValueError('Need at least five seasons for tuning and two-season holdout')
    holdout = years[-2:]
    eligible = frame[frame.points_pctile_lag1.notna()].copy()
    train = eligible[eligible.year < holdout[0]].copy()
    test = eligible[eligible.year.isin(holdout)].copy()
    if train.empty or test.empty:
        raise ValueError('Empty temporal split')
    return train, test


def rolling_folds(train):
    """Expanding origins; entire years stay together and validation is later."""
    years = sorted(train.year.unique())
    for year in years[1:]:
        yield train[train.year < year].copy(), train[train.year.eq(year)].copy()
