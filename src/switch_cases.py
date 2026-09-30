"""Descriptive provider-switch case studies; no counterfactual or causal estimates.

Calendar windows contain t=-2,-1,0,1,2. The transition season is t=0 and
counts as post; the cancelled 2019-20 season remains a missing calendar slot.
An evidence set supports a contrast only with at least one covered pre season
under the old provider and one covered post season under the new provider.
"""
from html import escape
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

EVIDENCE_SETS = {'primary': ('A', 'B', 'C'), 'sensitivity': ('A', 'B')}
BRANDS = ('Nike', 'adidas', 'Under Armour', 'other')


def _season(year):
    return f'{year}-{str(year + 1)[-2:]}'


def _brand_counts(rows):
    counts = rows.brand.value_counts()
    return '; '.join(f'{brand}: {int(counts.get(brand, 0))}' for brand in BRANDS)


def _link(url, label='source'):
    if pd.isna(url) or not url:
        return ''
    return f'<a href="{escape(str(url), quote=True)}">{escape(label)}</a>'


def _chart(rows, event, summaries, output):
    """Render every event, including unqualified cases, with explicit missingness."""
    fig, ax = plt.subplots(figsize=(8.4, 4.8), layout='constrained')
    fig.patch.set_facecolor('#faf9f5')
    ax.set_facecolor('#faf9f5')
    x = rows.relative_season.to_numpy()
    valid = rows.primary_included
    ax.plot(x, rows.points_pctile.where(valid), color='#245761', lw=2, zorder=2)
    direct = rows.evidence_tier.isin(['A', 'B']) & rows.outcome_available
    inferred = rows.evidence_tier.eq('C') & rows.outcome_available
    unknown = ~rows.evidence_tier.isin(['A', 'B', 'C']) & rows.outcome_available
    ax.scatter(rows.loc[direct, 'relative_season'], rows.loc[direct, 'points_pctile'],
               c='#245761', s=68, label='Tier A/B', zorder=3)
    if inferred.any():
        ax.scatter(rows.loc[inferred, 'relative_season'], rows.loc[inferred, 'points_pctile'],
                   c='#cf8642', marker='^', s=78, label='Tier C (inferred)', zorder=3)
    if unknown.any():
        ax.scatter(rows.loc[unknown, 'relative_season'], rows.loc[unknown, 'points_pctile'],
                   edgecolors='#858585', facecolors='none', s=68,
                   label='Outcome known; provider unknown', zorder=3)
    ax.axvline(-0.5, color='#b06c3c', lw=1.2, ls='--')
    for row in rows.itertuples():
        if not row.outcome_available:
            ax.axvspan(row.relative_season - 0.4, row.relative_season + 0.4,
                       color='#d9d7ce', alpha=.55, lw=0)
            label = 'COVID\nno final' if row.season == '2019-20' else 'Outside\ndata window'
            ax.text(row.relative_season, 5, label, ha='center', va='bottom', fontsize=8, color='#666')
        else:
            ax.annotate(f'{row.points_pctile:.1f}', (row.relative_season, row.points_pctile),
                        xytext=(0, 9), textcoords='offset points', ha='center', fontsize=9)
    ax.set(xlim=(-2.5, 2.5), ylim=(0, 106), ylabel='Points percentile (eligible panel)',
           xlabel='Calendar season relative to switch; t=0 is first post season')
    ax.set_xticks(x, [f'{r.relative_season:+d}\n{r.season}' for r in rows.itertuples()])
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.grid(axis='y', color='#dddcd3', lw=.7)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(loc='lower left', frameon=False, fontsize=8)
    status = 'Descriptive comparison' if summaries['primary']['usable'] else 'Insufficient covered pre/post data'
    fig.suptitle(f"{event['school']}: {event['previous_brand']} → {event['brand']}\n"
                 f"{event['season']} · {status}", fontsize=13, fontweight='bold')
    footer = '\n'.join(f"{'+'.join(EVIDENCE_SETS[k])}: {v['n_pre']} pre / {v['n_post']} post; {v['n_per_brand']}"
                       for k, v in summaries.items())
    fig.text(.02, -.055, footer + '\nDescriptive outcomes only. Changes cannot be attributed to the provider.',
             fontsize=8, va='top')
    for ext in ('png', 'svg'):
        fig.savefig(output.with_suffix('.' + ext), dpi=160, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)


def build_switch_cases(panel, root):
    """Write calendar-aligned charts, observations, usability and confounder tables.

    Parameters
    ----------
    panel : pandas.DataFrame
        All eligible school seasons, including unknown sponsors. Must contain
        school, season, brand, evidence_tier and either points_pctile_analysis or
        panel_points_pctile. Conference labels are supplied by the caller or
        normalized conservatively from the stored conference field.
    root : str or pathlib.Path
        Project directory with data/sponsor_transition_register.json and
        data/switch_confounders.json.

    Returns
    -------
    dict
        summary (one row per event/evidence set), observations (five calendar
        slots per event), confounders, and html_path. Summary differences are
        unadjusted post-minus-pre averages; they are not treatment effects.
    """
    root = Path(root)
    panel = panel.copy()
    required = {'school', 'season', 'brand', 'evidence_tier'}
    if not required.issubset(panel):
        raise ValueError(f'Missing switch panel columns: {sorted(required - set(panel))}')
    if panel.duplicated(['school', 'season']).any():
        raise ValueError('Switch cases require unique school-season outcomes')
    outcome = next((c for c in ('points_pctile_analysis', 'panel_points_pctile') if c in panel), None)
    if outcome is None:
        raise ValueError('Switch cases require the audited panel percentile outcome')
    if 'year' not in panel:
        panel['year'] = panel.season.str[:4].astype(int)
    if 'conference_model' not in panel:
        panel['conference_model'] = panel.conference.str.replace('Pac 12', 'Pac-12', regex=False)
    events = json.loads((root/'data/sponsor_transition_register.json').read_text())
    confounder_doc = json.loads((root/'data/switch_confounders.json').read_text())
    confounders = {r['school']: r for r in confounder_doc['schools']}
    report_dir = root/'reports'
    figure_dir = report_dir/'figures'
    figure_dir.mkdir(parents=True, exist_ok=True)
    tables, summaries, confounder_rows, cards = [], [], [], []
    for event in events:
        year = int(event['season'][:4])
        school = event['school']
        grid = pd.DataFrame({'year': range(year - 2, year + 3)})
        fields = ['year', 'season', 'brand', 'evidence_tier', outcome, 'conference_model']
        rows = grid.merge(panel.loc[panel.school.eq(school), fields], on='year', how='left', validate='one_to_one')
        rows['school'] = school
        rows['season'] = rows.year.map(_season)
        rows['relative_season'] = rows.year - year
        rows['from_brand'] = event['previous_brand']
        rows['to_brand'] = event['brand']
        rows['switch_season'] = event['season']
        rows['transition_date'] = event.get('transition_date')
        rows['transition_date_precision'] = event.get('date_precision')
        rows = rows.rename(columns={outcome: 'points_pctile'})
        rows['outcome_available'] = rows.points_pctile.notna()
        rows['evidence_tier'] = rows.evidence_tier.fillna('unknown')
        rows['expected_brand'] = np.where(rows.relative_season.lt(0), event['previous_brand'], event['brand'])
        rows['provider_matches_event'] = rows.brand.eq(rows.expected_brand)
        local_summaries = {}
        for name, tiers in EVIDENCE_SETS.items():
            rows[name + '_included'] = rows.outcome_available & rows.evidence_tier.isin(tiers) & rows.provider_matches_event
            keep = rows.loc[rows[name + '_included']]
            pre = keep.loc[keep.relative_season.lt(0)]
            post = keep.loc[keep.relative_season.ge(0)]
            usable = len(pre) > 0 and len(post) > 0
            reason = ('At least one covered season on each side; descriptive only.' if usable else
                      'No covered pre-switch season under the documented former provider within ±2 seasons.' if pre.empty else
                      'No covered post-switch season under the documented new provider within ±2 seasons.')
            result = {'school': school, 'switch_season': event['season'], 'from_brand': event['previous_brand'],
                      'to_brand': event['brand'], 'transition_date': event.get('transition_date'),
                      'transition_date_precision': event.get('date_precision'), 'evidence_set': name,
                      'tiers_used': '+'.join(tiers), 'usable': usable, 'reason': reason,
                      'n_pre': len(pre), 'n_post': len(post), 'n_school_seasons': len(keep),
                      'n_per_brand': _brand_counts(keep), 'pre_mean_points_pctile': pre.points_pctile.mean(),
                      'post_mean_points_pctile': post.points_pctile.mean(),
                      'descriptive_change': post.points_pctile.mean() - pre.points_pctile.mean() if usable else np.nan,
                      'n_tier_a': int(keep.evidence_tier.eq('A').sum()), 'n_tier_b': int(keep.evidence_tier.eq('B').sum()),
                      'n_tier_c': int(keep.evidence_tier.eq('C').sum()), 'transition_source_url': event['source_url']}
            for brand in BRANDS:
                result['n_' + brand.lower().replace(' ', '_')] = int(keep.brand.eq(brand).sum())
            summaries.append(result)
            local_summaries[name] = result
        for name in EVIDENCE_SETS:
            rows['usable_' + name] = local_summaries[name]['usable']
        covid_gap = year - 2 <= 2019 <= year + 2
        covid_disruption = year - 2 <= 2020 <= year + 2
        conf = confounders[school].copy()
        conf['switch_season'] = event['season']
        conf['covid_gap'] = covid_gap
        conf['covid_note'] = ('2019-20 was cancelled and has no annual final; preserve the calendar gap. ' if covid_gap else '') + (
            '2020-21 pandemic disruptions also fall in this window.' if covid_disruption else 'No 2019-20/2020-21 season in this window.')
        conf['observed_conferences'] = ' → '.join(rows.loc[rows.outcome_available, 'conference_model'].dropna().drop_duplicates())
        conf['observed_realignment'] = rows.loc[rows.outcome_available, 'conference_model'].nunique() > 1
        conf['coaching_screen_limit'] = confounder_doc['scope']
        confounder_rows.append(conf)
        tables.append(rows)
        slug = re.sub(r'[^a-z0-9]+', '_', school.lower()).strip('_')
        figure = figure_dir/f'switch_case_{slug}'
        _chart(rows, event, local_summaries, figure)
        small = []
        for name, result in local_summaries.items():
            delta = f"{result['descriptive_change']:+.2f}" if result['usable'] else 'Not estimated'
            small.append(f"<tr><td>{result['tiers_used']}</td><td>{result['n_pre']}</td><td>{result['n_post']}</td>"
                         f"<td>{delta}</td><td>{escape(result['n_per_brand'])}</td></tr>")
        cards.append(f'''<section id="{slug}"><h2>{escape(school)}</h2>
<p>{escape(event['previous_brand'])} → {escape(event['brand'])}; first post season {escape(event['season'])}.
Transition date: {escape(str(event.get('transition_date', 'unknown')))} ({escape(event.get('date_precision', ''))}).
{_link(event['source_url'], 'Provider source')}</p>
<img src="figures/{figure.name}.png" alt="{escape(school)} performance before and after the provider switch">
<table><thead><tr><th>Evidence tiers</th><th>n pre</th><th>n post</th><th>Post − pre, percentile points</th><th>n per brand</th></tr></thead><tbody>{''.join(small)}</tbody></table>
<p>{escape(local_summaries['primary']['reason'])} {escape(event.get('notes', ''))}</p>
<p><strong>COVID:</strong> {escape(conf['covid_note'])}<br>
<strong>Realignment:</strong> {escape(conf['realignment_note'])} {_link(conf.get('realignment_source_url'))}<br>
<strong>Coaching:</strong> {escape(conf['coaching_change'])} {_link(conf.get('coaching_source_url'))}</p></section>''')
    summary = pd.DataFrame(summaries)
    observations = pd.concat(tables, ignore_index=True)
    confounder_table = pd.DataFrame(confounder_rows)
    summary.to_csv(report_dir/'switch_case_summary.csv', index=False)
    observations.to_csv(report_dir/'switch_case_observations.csv', index=False)
    confounder_table.to_csv(report_dir/'switch_case_confounders.csv', index=False)
    usable_counts = summary.groupby('tiers_used').usable.sum()
    counts_text = '; '.join(f'{tiers}: {count} of {len(events)} usable' for tiers, count in usable_counts.items())
    confounder_html = '<table><thead><tr><th>School</th><th>COVID gap</th><th>Realignment</th><th>Coaching screen</th></tr></thead><tbody>' + ''.join(
        f"<tr><td>{escape(row['school'])}</td><td>{escape(row['covid_note'])}</td><td>{escape(row['realignment_note'])} {_link(row.get('realignment_source_url'))}</td><td>{escape(row['coaching_change'])} {_link(row.get('coaching_source_url'))}</td></tr>"
        for row in confounder_rows) + '</tbody></table>'
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Provider switch case studies</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;background:#faf9f5;color:#20343b;max-width:1100px;margin:40px auto;padding:0 24px}}h1{{font-size:34px}}h2{{font-size:25px}}section{{border-top:1px solid #ccc;padding:26px 0}}img{{width:100%;max-width:900px}}table{{border-collapse:collapse;width:100%;font-size:14px;margin:16px 0}}th,td{{border-bottom:1px solid #d7d5cb;padding:10px;text-align:left}}a{{color:#236d80}}.callout{{padding:20px;background:#e9efeb}}</style></head><body>
<h1>Provider switches: ten descriptive case studies</h1>
<p>Department-level all-sports Directors' Cup outcomes; windows of up to ±2 calendar seasons. {escape(counts_text)}.</p>
<div class="callout"><strong>Supporting evidence, not causal tests.</strong> A usable case has at least one covered pre season and one covered post season under the documented providers. The switch season is t=0 and is counted as post. The window includes t=−2 through +2 (up to two pre and three post seasons). Missing 2019-20 outcomes are not bridged or shifted. Post-minus-pre means are unadjusted descriptions.</div>
<p>The chart outcome is the annual percentile in the audited eligible school panel, including retained zero rows. It is not a causal effect and its denominator is the study's observed-school universe, not a claim to include every Division I institution. Coaching notes are a targeted screen, not an exhaustive review of every team; blank or unestablished changes do not imply stability.</p>
<p><a href="switch_case_summary.csv">Case summary CSV</a> · <a href="switch_case_observations.csv">Calendar-aligned observations CSV</a> · <a href="switch_case_confounders.csv">Confounder table CSV</a></p>
<h2>Confounders within the available window</h2>{confounder_html}
{''.join(cards)}</body></html>'''
    html_path = report_dir/'switch_case_studies.html'
    html_path.write_text(html)
    return {'summary': summary, 'observations': observations, 'confounders': confounder_table, 'html_path': html_path}
