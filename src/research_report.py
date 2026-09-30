"""Reproducible tiered research audit; unknown and inferred remain distinct."""
import json
from html import escape
import pandas as pd

STYLE = '''body{font:16px/1.55 system-ui,sans-serif;color:#172322;background:#f6f7f4;margin:0}main{max-width:1200px;padding:40px 24px;margin:auto}h1{font-size:clamp(30px,5vw,52px);line-height:1.1}h2{margin-top:36px}a{color:#00645b}p{max-width:980px}.cards{display:flex;gap:16px;flex-wrap:wrap}.cards div{background:white;padding:20px;flex:1;min-width:140px}.cards strong{display:block;font-size:34px}.cards span{font-size:14px}.scroll{overflow:auto}table{border-collapse:collapse;background:white;width:100%;font-size:14px}td,th{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #d9dfda}td p{margin:8px 0 0}td a{margin-right:10px}.note{border-left:4px solid #be7516;padding:14px 18px;background:#fff4dc}.muted{color:#59665f}'''


def write_research_report(root, coverage, evidence, switches, summary):
    reviews = coverage.groupby('school').agg(
        covered_seasons=('covered','sum'),
        verified_seasons=('evidence_tier', lambda x:x.isin(['A','B']).sum()),
        tier_A=('evidence_tier',lambda x:x.eq('A').sum()),
        tier_B=('evidence_tier',lambda x:x.eq('B').sum()),
        tier_C=('evidence_tier',lambda x:x.eq('C').sum())).reset_index()
    missing = coverage[coverage.evidence_tier.eq('unknown')].groupby('school').season.agg(', '.join)
    reviews['missing_seasons'] = reviews.school.map(missing).fillna('')
    reviews['research_status'] = reviews.covered_seasons.eq(8).map({True:'reviewed_full_coverage',False:'reviewed_partial_coverage'})
    reviews['required_followup'] = reviews.missing_seasons.ne('').map({True:'Unknown retained; future dated official evidence needed. Research stopped at the agreed 90% threshold.',False:'None for threshold; C remains inferred and is excluded from sensitivity analysis.'})
    reviews['source_urls'] = reviews.school.map(evidence.groupby('school').source_url.agg(lambda x:' | '.join(sorted(set(x))))).fillna('')
    reviews.to_csv(root/'reports/sponsor_research_review.csv',index=False)
    events = pd.DataFrame(json.loads((root/'data/sponsor_transition_register.json').read_text())).sort_values(['season','school'])
    assert len(events)==10 and not events.duplicated(['school','season']).any()
    events.to_csv(root/'reports/sponsor_switch_events.csv',index=False)
    conflicts = pd.DataFrame(json.loads((root/'data/sponsor_source_conflicts.json').read_text()))
    conflicts.to_csv(root/'reports/sponsor_source_conflicts.csv',index=False)
    summary.update(reviewed_priority_schools=len(reviews),documented_switch_events=len(events))
    cards=''.join(f'<div><strong>{value}</strong><span>{label}</span></div>' for label,value in [
        ('Coverage A+B+C',f'{summary["coverage_percent"]:.1f}%'),('Tier A',summary['evidence_tier_counts'].get('A',0)),
        ('Tier B',summary['evidence_tier_counts'].get('B',0)),('Tier C · inferred',summary['evidence_tier_counts'].get('C',0)),
        ('Unknown',summary['unknown_priority_school_seasons'])])
    rows=[]
    for r in reviews.sort_values(['covered_seasons','school']).to_dict('records'):
        links=' '.join(f'<a href="{escape(u,quote=True)}">Source {i+1}</a>' for i,u in enumerate(r['source_urls'].split(' | ')) if u)
        rows.append(f'<tr><th>{escape(r["school"])}</th><td>{r["covered_seasons"]}/8</td><td>{r["tier_A"]} / {r["tier_B"]} / {r["tier_C"]}</td><td>{escape(r["missing_seasons"]) or "—"}</td><td>{links or "No qualifying evidence"}</td></tr>')
    season_rows=[]
    for r in coverage.sort_values(['school','season']).to_dict('records'):
        tier=r['evidence_tier']
        if tier=='unknown': continue
        if tier=='C':
            links=f'<a href="{escape(r["left_anchor_url"],quote=True)}">{r["left_anchor_season"]} anchor</a> · <a href="{escape(r["right_anchor_url"],quote=True)}">{r["right_anchor_season"]} anchor</a>'
        else:
            links=f'<a href="{escape(r["source_url"],quote=True)}">Evidence</a>'
            date=r.get('snapshot_date') or r.get('source_date')
            if pd.notna(date): links+=f' · dated {escape(str(date))}'
        season_rows.append(f'<tr><th>{escape(r["school"])}</th><td>{r["season"]}</td><td>{escape(r["brand"])} · {tier}</td><td>{escape(str(r["source_type"]))}<p>{links}</p>{escape(str(r["evidence_summary"]))}</td></tr>')
    html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>The Swoosh Effect — Research audit</title><style>{STYLE}</style><main>
<p>THE SWOOSH EFFECT · SOURCE AUDIT · 30 SEPTEMBER 2026</p><h1>All-sports research.<br>Evidence you can trace.</h1>
<p>The outcome is each athletic department’s official Directors’ Cup total across sports. Exposure is its primary apparel provider; team exceptions are documented but are not separate model assignments.</p>
<div class="cards">{cards}</div>
<p class="note"><b>Research threshold reached: {summary['covered_priority_school_seasons']} of {len(coverage)} school-seasons.</b> Sponsorship research stopped at 90.7%, before Phase 3. Direct evidence A+B covers {summary['direct_priority_school_seasons']} seasons (78.9%); continuity adds 70. Unknowns remain unknown. {summary['fully_covered_priority_schools']} of 74 schools have eight covered seasons.</p>
<h2>The evidence rules</h2><ul>
<li><b>A:</b> contract, board record, official announcement or previously accepted reporting of contract terms. Secondary reporting is retained with its source type labeled.</li>
<li><b>B:</b> dated official evidence of provider use within that season: archived partner/footer, media guide, game notes or athletics release. Archive URLs and actual snapshot dates are retained. A dated team publication corroborates an established department provider; it does not establish a separate team exposure.</li>
<li><b>C:</b> explicitly inferred between A/B anchors for the same brand, with no known intervening switch in reviewed evidence. Never extrapolated to either window endpoint, and never used as an anchor itself.</li>
<li><b>Unknown:</b> no qualifying assignment. The 55 unknowns are excluded from both models, not recoded as “other.”</li></ul>
<p>Primary analysis uses A+B+C; sensitivity uses A+B. Nike/Jordan is one provider family. Payment disputes do not change apparel-provider assignments and do not demonstrate payment continuity. Department totals cannot isolate equipment or team-specific effects.</p>
<p>The eight seasons span 2017–18 through 2025–26, excluding cancelled 2019–20. Research scope is 74 schools: current Power 4 plus other schools that reached the top 50. This is a selected cohort, not all Division I departments. The public evidence tables retain canonical source URLs, Wayback snapshot URLs, dates and source types. Raw third-party pages and search/retrieval logs are excluded from this repository; only accepted evidence drives assignments.</p>
<h2>Transition-season decisions</h2><p>Boston College stays Under Armour for 2020–21: most competition preceded the June 1, 2021 New Balance launch. New Balance becomes the primary department provider in 2021–22; football was initially excepted. Florida stays Nike for 2023–24: the cited term extends to April 1, 2024, covering fall and winter and the beginning of spring. That contract endpoint is not evidence of a provider switch; later Nike use is documented. The ten-event register records dates and date precision. Denver’s June 3, 2025 date is an announcement date, not a verified first-use day.</p>
<h2>Zero-row audit</h2><p>Reviewed all {summary['zero_rows_reviewed']} imputed rows across 155 programs: <b>{summary['zero_rows_kept']} kept, {summary['zero_rows_dropped']} dropped</b>. Retain known D1 programs during D1 competition, including reclassification years with possible postseason restrictions. Drop pre-entry years and years after Hartford’s DIII move or St. Francis Brooklyn’s closure. Established programs are supported by official D1 standings elsewhere in the window and an entry/exit review; these are not 469 independently certified annual membership records. A zero denotes no Cup points, not proof a team competed normally—COVID cancellations matter.</p>
<p>The retained panel has {summary['panel_rows']:,} rows. Its percentile is recomputed within season after removing ineligible zeros. Original published-school percentiles remain unchanged in a separate column. Schools that never appeared in any input final standings are outside this panel.</p>
<p><a href="zero_row_audit.csv">All 469 zero decisions</a> · <a href="../data/division_i_membership_review.csv">Membership evidence</a> · <a href="https://ncaaorg.s3.amazonaws.com/research/sportpart/2023-24RES_NCAAMembershipBreakdown.pdf">NCAA transition reference</a></p>
<h2>School coverage</h2><div class="scroll"><table><thead><tr><th>School</th><th>Covered</th><th>A / B / C</th><th>Unknown seasons</th><th>Sources</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>Season-level provenance</h2><details><summary>Expand all {summary['covered_priority_school_seasons']} covered school-seasons</summary><div class="scroll"><table><thead><tr><th>School</th><th>Season</th><th>Provider · tier</th><th>Source type, dates and limits</th></tr></thead><tbody>{''.join(season_rows)}</tbody></table></div></details>
<h2>Conflicts and completed analysis</h2><p>Iowa State’s conflicting expiration dates remain unresolved; only its supported 2017–18 assignment is retained. Stale Rutgers and incorrect West Virginia entries were rejected. The completed analysis evaluates ten documented transitions for covered pre/post outcomes, realignment, COVID gaps and coaching changes. Nine are usable as descriptive case studies; Denver lacks covered pre-switch evidence. See the <a href="phase3_analysis.html">analysis report</a> and <a href="switch_case_studies.html">switch case studies</a>. These patterns are consistent with selection and persistence, not proof of causation.</p>
<p><a href="sponsor_coverage.csv">Season evidence CSV</a> · <a href="sponsor_research_review.csv">School review CSV</a> · <a href="sponsor_switch_events.csv">Ten-event register</a> · <a href="sponsor_source_conflicts.csv">Source conflicts</a></p></main></html>'''
    (root/'reports/sponsor_research.html').write_text(html)
