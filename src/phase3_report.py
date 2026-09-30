"""Render analysis results and a runnable notebook from the same computed tables."""
import json
import pandas as pd
from .research_report import STYLE


def html_table(data):
    return '<div class="scroll">'+data.to_html(index=False,border=0,float_format=lambda x:f'{x:.2f}',na_rep='—')+'</div>'


def write_report(root,tables,cases):
    coef=tables['model_coefficients'];samples=tables['model_sample_sizes'];desc=tables['brand_summary']
    brand_order=['Nike','adidas','Under Armour','other']
    comparison=[];attenuation=[]
    for b in brand_order:
        row={'Brand':b}
        for tiers in ['A+B+C','A+B']:
            for model in ['plain','lagged']:
                s=samples[(samples.evidence_tiers==tiers)&(samples.model==model)&(samples.brand==b)].iloc[0]
                if b=='Nike':value='Reference'
                else:
                    c=coef[(coef.evidence_tiers==tiers)&(coef.model==model)&(coef.brand==b)].iloc[0]
                    value=f'{c.coefficient:+.2f} [{c.ci_low:+.2f}, {c.ci_high:+.2f}]'
                row[f'{tiers} · {model}']=f'{value}; n={int(s.n)}'
        comparison.append(row)
    for tiers in ['A+B+C','A+B']:
        for b in ['adidas','Under Armour']:
            before=coef[(coef.evidence_tiers==tiers)&(coef.model=='plain_matched')&(coef.brand==b)].iloc[0]
            after=coef[(coef.evidence_tiers==tiers)&(coef.model=='lagged')&(coef.brand==b)].iloc[0]
            attenuation.append({'Evidence':tiers,'Brand versus Nike':b,'Plain, matched rows':before.coefficient,
                'Lagged, same rows':after.coefficient,'Magnitude shrinkage %':100*(1-abs(after.coefficient/before.coefficient)),
                'Model n':int(after.n)})
    comparison=pd.DataFrame(comparison);attenuation=pd.DataFrame(attenuation)
    comparison.to_csv(root/'reports/model_comparison.csv',index=False)
    attenuation.to_csv(root/'reports/lag_attenuation.csv',index=False)
    descriptive=desc[['evidence_tiers','brand','n_school_seasons','n_schools','mean_percentile','median_percentile','mean_points','median_points','n_tier_A','n_tier_B','n_tier_C']]
    share=tables['brand_shares'];share=share[share.season.eq('All seasons')][['evidence_tiers','universe','brand','n','denominator','share_pct']]
    missing=pd.read_csv(root/'reports/sponsor_research_review.csv');missing=missing[missing.missing_seasons.notna()]
    missing=missing[['school','missing_seasons']]
    summary=cases['summary'][['school','tiers_used','usable','n_pre','n_post','descriptive_change','n_per_brand','reason']]
    html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>The Swoosh Effect — Phase 3</title><style>{STYLE}img{{max-width:100%;height:auto;background:white}}code{{background:#e7ece8;padding:2px 4px}}.scroll{{margin:18px 0}}details{{margin:20px 0}}</style><main>
<p>THE SWOOSH EFFECT · PHASE 3 · 30 SEPTEMBER 2026</p><h1>Winning persists.<br>The brand gap shrinks.</h1>
<p>Nike schools have the highest average performance in the covered research cohort. Once prior-season performance is included, their adjusted advantage over adidas and Under Armour becomes smaller under both evidence standards. These associations are consistent with persistent strength and selection into sponsorship; they do not establish who caused that strength.</p>
<p class="note"><b>Primary: A+B+C, 537 school-seasons / 73 schools. Sensitivity: A+B, 467 / 73.</b> Lagged models use 401 and 341 school-seasons, respectively, across 72 schools. All schools with usable provider evidence are included, not only switchers. Unknown-brand rows are not guessed into a brand group. The broader performance panel contains 358 institutions, but sponsorship coverage remains focused on 74.</p>
<h2>Brand comparison</h2><img src="figures/brand_comparison.png" alt="Average performance by brand under both evidence standards, with sample counts">
{html_table(descriptive)}
<p>Each row is an athletic-department season. Percentile is 100 × average ascending rank of total points / eligible programs in that season’s observed-ever universe, including 438 reviewed zeros and excluding 31 invalid zeros. It is not an all-D1 census. The mean raw points are supplementary; percentiles are used for comparisons across seasons. Nike includes Jordan; “other” groups known smaller providers and is not a missing-value category.</p>
<h2>Plain and lagged models, side by side</h2>
<p>Coefficients below are <b>percentile-point differences relative to Nike</b>; negative means a lower predicted percentile than Nike, conditional on the included controls. Brackets show 95% confidence intervals. Standard errors cluster by school, with a small-sample covariance correction and t inference using school clusters minus one degrees of freedom.</p>
{html_table(comparison)}
<img src="figures/controlled_models.png" alt="Plain, matched-sample plain, and lagged regression estimates with 95 percent intervals and per-brand sample counts">
<p><code>percentile(t) ~ brand + conference(t) + season</code><br><code>percentile(t) ~ brand + percentile(t−1) + conference(t) + season</code></p>
<p>The lag is the previous <b>calendar</b> season. There is no 2016–17 input, and cancelled 2019–20 is excluded; therefore 2017–18 and 2020–21 cannot enter the lagged model. A prior outcome may be used even when that prior season’s provider is unknown. Source conferences are season-specific; Pac 12/Pac-12 spelling is normalized. Yale’s 2020–21 zero uses the Ivy League classification supported on both sides; its source conference stays blank and the modeling assumption is labeled.</p>
<p><b>“Other” is a sparse group:</b> seven seasons from three schools in the plain model, and five seasons from Boston College alone in the lagged model. Its mechanically computed interval is not reliable evidence about a general category of smaller brands. Repeated observations do not create independent schools.</p>
<h2>The pick-versus-make check</h2><p>The fair shrinkage comparison holds the rows constant. The additional <code>plain_matched</code> fit uses exactly the lagged model’s sample, without the lag predictor.</p>
{html_table(attenuation)}
<p>On matched rows, the Nike-relative adidas and Under Armour coefficient magnitudes shrink by about <b>62–68% with A+B+C</b> and <b>56–62% with A+B</b>. Both brands’ lagged-model intervals include zero in both versions. Prior-performance coefficients are 0.59 [0.35, 0.83] and 0.56 [0.30, 0.81], respectively. The continuity inference changes estimates modestly without changing this conclusion.</p>
<p>This supports a cautious <b>“pick / persistence” interpretation</b>, rather than evidence that a provider makes departments improve. It is not proof of Nike’s selection strategy. Athletic budgets, sport offerings, coaching, recruitment and institutional advantages remain omitted; prior performance may itself reflect earlier sponsor exposure. A nonzero coefficient would still be an association, and an interval containing zero does not prove no effect. These models have conference and season effects, not school fixed effects, and are not validated forecasting models.</p>
<h2>Provider shares and top finishes</h2><p>Denominators include all rows in the stated universe, including unassigned providers. “Ranked D1” means published final-standings rows, not the full D1 membership. “Current Power 4 cohort” follows the same 68 schools identified in 2025–26 back through the window; it is not a claim those schools were always in those conferences. Top-10 and top-25 shares use all official finishes at those ranks, including unassigned brands. n is school-seasons or finishes.</p>
<details><summary>Expand brand shares, sample sizes and denominators</summary>{html_table(share)}</details>
<h2>Switches are supporting case studies</h2><p>Use up to two calendar seasons before and two after each first new-provider season; t=0 is the first post-switch season. Require at least one covered pre and one covered post observation for a before/after description. No outcome is manufactured for 2019–20, and no switch date is moved to hide a missing year. These are descriptive histories, with no causal claims or difference-in-differences estimates.</p>
<p><a href="switch_case_studies.html">Open all ten school charts, eligibility decisions, sample counts and confounders</a></p>
{html_table(summary)}
<h2>Women’s rowing: a limited supporting cut</h2><p>Only positive published NCAA rowing scores enter this table. It compares scoring school-seasons, not all rowing programs or a team’s probability of qualifying. The provider is the department’s primary brand; individual team exceptions are not modeled. Unassigned rows remain visible, and are not included in the brand coefficients above.</p>
{html_table(tables['rowing_summary'])}
<h2>Unverified or assumed</h2><ul>
<li>55 priority school-seasons remain unknown; sponsorship outside the 74-school research scope was not completed. The cohort is selective, and “all covered schools” is not all D1.</li>
<li>70 Tier C seasons are continuity inferences. Tier A retains labeled secondary contract reporting; Tier B uses dated official use. Neither establishes all amendments or actual payment amounts.</li>
<li>Team exceptions and provider-payment disputes are documented but are not separate exposure variables. Continued use is not continuing payment.</li>
<li>The 438 zeros use reviewed D1 program intervals. Some reflect COVID cancellations or postseason restrictions. Institutions never appearing in any input final standings are outside the panel.</li>
<li>Switch coaching flags are a limited screen, not an audit of every sport or staff change. Realignment and COVID affect interpretation.</li>
<li>Revenue and other department resources are not controlled. Private-school revenue gaps remain; the optional Knight–Newhouse robustness check was not run.</li>
<li>Earlier per-sport reconciliation limitations remain; all-sports analysis uses official annual totals, not a reconstruction from incomplete sport contributions.</li></ul>
<details><summary>Unknown priority seasons by school</summary>{html_table(missing)}</details>
<h2>Reproduce and inspect</h2><p>Run <code>python -m src.analyze</code> after building the database. The notebook <code>notebooks/analysis.ipynb</code> runs the same analysis and displays its tables. Every result CSV carries evidence tiers and sample counts. Source lineage lives in the <a href="sponsor_research.html">research audit</a>.</p>
<p><a href="model_coefficients.csv">All coefficients and intervals</a> · <a href="model_sample_sizes.csv">Per-brand sample sizes and tiers</a> · <a href="model_diagnostics.csv">Model specifications</a> · <a href="brand_summary.csv">Brand summaries</a> · <a href="brand_shares.csv">Shares by season</a> · <a href="rowing_scoring_rows.csv">Rowing source rows</a></p>
<p class="muted">Method reference: <a href="https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html">statsmodels clustered covariance documentation</a>. Installed version and numeric-library versions are recorded in analysis_validation.json.</p></main></html>'''
    (root/'reports/phase3_analysis.html').write_text(html)
    write_notebook(root,comparison,attenuation,descriptive)


def write_notebook(root,comparison,attenuation,descriptive):
    cells=[]
    def md(s):cells.append({'id':f'cell-{len(cells)}','cell_type':'markdown','metadata':{},'source':s.splitlines(True)})
    def code(s,output=None):
        outputs=[] if output is None else [{'output_type':'display_data','data':{'text/html':[output.to_html(index=False)],'text/plain':[output.to_string(index=False)]},'metadata':{}}]
        cells.append({'id':f'cell-{len(cells)}','cell_type':'code','metadata':{},'execution_count':None,'source':s.splitlines(True),'outputs':outputs})
    md('# The Swoosh Effect — Phase 3\n\nDepartment-level all-sports results. Primary A+B+C; sensitivity A+B.\nRun all cells with the project environment. Cached tables below are generated by the same analysis script; no causal interpretation is warranted.')
    code("from pathlib import Path\nimport sys\nimport pandas as pd\nfrom IPython.display import display, Image\nROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\nsys.path.insert(0, str(ROOT))\nfrom src.analyze import analyze\ntables = analyze()")
    md('## Descriptive comparison\nCounts are school-seasons; the 74-school research scope is selected. Percentiles include only reviewed eligible zeros.')
    code("display(tables['brand_summary'])\ndisplay(Image(filename=str(ROOT / 'reports/figures/brand_comparison.png')))",descriptive)
    md('## Plain and lagged models\nCoefficients compare other brands with Nike. Conference and season fixed effects; school-clustered SE and 95% intervals. Lag joins use actual calendar years, never bridge excluded 2019–20.')
    code("display(pd.read_csv(ROOT / 'reports/model_comparison.csv'))\ndisplay(tables['model_sample_sizes'])\ndisplay(Image(filename=str(ROOT / 'reports/figures/controlled_models.png')))",comparison)
    md('## Matched-sample attenuation\nCompare the plain and lagged model on exactly the same rows. Shrinkage is consistent with persistence/selection, not proof of how Nike selects schools. A remaining coefficient would not prove a causal improvement.')
    code("display(pd.read_csv(ROOT / 'reports/lag_attenuation.csv'))",attenuation)
    md('## Descriptive switches and rowing\nUp to ±2 calendar seasons; at least one covered pre and post. t=0 is post. Confounders are flagged; no DiD or causal claim. Rowing includes positive published scores only, not all rowing programs.')
    code("display(pd.read_csv(ROOT / 'reports/switch_case_summary.csv'))\ndisplay(tables['rowing_summary'])")
    md('## Limits and sources\n55 priority seasons unknown; 70 Tier C inferences; scope excludes unresearched providers. No revenue adjustment. Sparse other-brand group (one school in lagged fits). Known-D1 zeros can reflect cancellations or postseason restrictions. Full source lineage and limitations: [research audit](../reports/sponsor_research.html), [Phase 3 report](../reports/phase3_analysis.html), [switch charts](../reports/switch_case_studies.html).')
    folder=root/'notebooks';folder.mkdir(exist_ok=True)
    (folder/'analysis.ipynb').write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}},'nbformat':4,'nbformat_minor':5},indent=2)+'\n')
