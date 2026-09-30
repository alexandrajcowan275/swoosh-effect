"""Phase 3: descriptive associations and lagged performance; never causal effects."""
import json
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/.matplotlib-cache'))
import numpy as np
import pandas as pd
import duckdb
import statsmodels
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

VERSIONS = {'A+B+C':['A','B','C'], 'A+B':['A','B']}
BRANDS = ['Nike','adidas','Under Armour','other']
FORMULA = 'panel_points_pctile ~ C(brand, Treatment(reference="Nike")) + C(conference_model) + C(season)'


def prepare_panel(panel):
    panel=panel.copy()
    panel['year']=panel.season.str[:4].astype(int)
    panel['conference_model']=panel.conference.replace({'Pac 12':'Pac-12'})
    panel['conference_basis']='official final standings; spelling normalized'
    # Only the two scoped Ivy zeros lack a printed conference. Both neighboring
    # observations must agree before using that conference for the zero year.
    for index,row in panel[panel.in_research_scope & panel.conference_model.isna()].iterrows():
        h=panel[(panel.school_id==row.school_id)&panel.conference_model.notna()]
        left=h[h.year<row.year].sort_values('year');right=h[h.year>row.year].sort_values('year')
        assert not left.empty and not right.empty and left.iloc[-1].conference_model==right.iloc[0].conference_model
        panel.loc[index,'conference_model']=left.iloc[-1].conference_model
        panel.loc[index,'conference_basis']='zero year; identical official conference in nearest prior and next standings'
    # Join on actual year, not row offset: 2018-19 is NOT the lag of 2020-21.
    lag=panel[['school_id','year','panel_points_pctile']].rename(columns={'panel_points_pctile':'lag_points_pctile'})
    lag['year']+=1
    panel=panel.merge(lag,on=['school_id','year'],how='left',validate='one_to_one')
    assert panel.loc[panel.year.eq(2020),'lag_points_pctile'].isna().all()
    return panel


def brand_counts(frame):
    return {b:int(frame.brand.eq(b).sum()) for b in BRANDS}


def fit_models(panel):
    coefficients=[]; samples=[]; diagnostics=[]
    for tiers,allowed in VERSIONS.items():
        full=panel[panel.in_research_scope & panel.evidence_tier.isin(allowed)].copy()
        lagged=full[full.lag_points_pctile.notna()].copy()
        assert full.conference_model.notna().all()
        for name,d,formula in [('plain',full,FORMULA),('plain_matched',lagged,FORMULA),('lagged',lagged,FORMULA+' + lag_points_pctile')]:
            model=smf.ols(formula,data=d,missing='raise').fit(cov_type='cluster',cov_kwds={
                'groups':d.school_id,'use_correction':True,'df_correction':True},use_t=True)
            assert np.linalg.matrix_rank(model.model.exog)==model.model.exog.shape[1], 'Rank deficient design'
            ci=model.conf_int()
            for term,coef in model.params.items():
                brand=next((b for b in BRANDS if term.endswith(f'[T.{b}]') and term.startswith('C(brand')),'')
                coefficients.append(dict(evidence_tiers=tiers,model=name,term=term,brand=brand,
                    coefficient=float(coef),ci_low=float(ci.loc[term,0]),ci_high=float(ci.loc[term,1]),
                    p_value=float(model.pvalues[term]),n=int(model.nobs),n_schools=d.school_id.nunique(),
                    n_per_brand=json.dumps(brand_counts(d),sort_keys=True),
                    n_tier_A=int(d.evidence_tier.eq('A').sum()),n_tier_B=int(d.evidence_tier.eq('B').sum()),n_tier_C=int(d.evidence_tier.eq('C').sum())))
            for b,g in d.groupby('brand'):
                samples.append(dict(evidence_tiers=tiers,model=name,brand=b,n=len(g),n_schools=g.school_id.nunique(),
                    n_A=int(g.evidence_tier.eq('A').sum()),n_B=int(g.evidence_tier.eq('B').sum()),n_C=int(g.evidence_tier.eq('C').sum())))
            diagnostics.append(dict(evidence_tiers=tiers,model=name,n=len(d),n_schools=d.school_id.nunique(),
                r_squared=float(model.rsquared),formula=formula,cluster_df=int(model.df_resid_inference),
                excluded_missing_lag=len(full)-len(lagged) if name!='plain' else 0))
    return pd.DataFrame(coefficients),pd.DataFrame(samples),pd.DataFrame(diagnostics)


def shares(panel,scope):
    current_p4=set(scope.loc[scope.power4_2025_26,'school'])
    results=[]
    for tiers,allowed in VERSIONS.items():
        p=panel.copy();p['assigned_brand']=p.brand.where(p.evidence_tier.isin(allowed),'Unassigned')
        universes={'Ranked D1':p[p.observed_in_final],
            'Current Power 4 cohort':p[p.school.isin(current_p4)],
            'Top 10 finishes':p[p['rank']<=10], 'Top 25 finishes':p[p['rank']<=25]}
        for universe,d in universes.items():
            for season,g in [('All seasons',d),*list(d.groupby('season'))]:
                for b,h in g.groupby('assigned_brand'):
                    results.append(dict(evidence_tiers=tiers,universe=universe,season=season,brand=b,
                        n=len(h),denominator=len(g),share_pct=100*len(h)/len(g),n_schools=h.school_id.nunique()))
    return pd.DataFrame(results)


def rowing_summary(con,panel):
    # Positive published women's-rowing scores, not all departments with rowing.
    rows=con.sql("SELECT * FROM sport_points WHERE sport='Women''s Rowing' AND points_basis='final_publication' AND sport_points>0").df()
    assert not rows.duplicated(['school_id','season']).any()
    rows=rows.merge(panel[['school_id','season','school','brand','evidence_tier','in_research_scope']],on=['school_id','season'],validate='one_to_one')
    result=[]
    for tiers,allowed in VERSIONS.items():
        d=rows.copy();d['assigned_brand']=d.brand.where(d.evidence_tier.isin(allowed),'Unassigned')
        for brand,g in d.groupby('assigned_brand'):
            result.append(dict(evidence_tiers=tiers,brand=brand,n=len(g),n_schools=g.school_id.nunique(),
                mean_rowing_points=g.sport_points.mean(),median_rowing_points=g.sport_points.median(),
                total_rowing_points=g.sport_points.sum(),n_A=int(g.evidence_tier.eq('A').sum()),
                n_B=int(g.evidence_tier.eq('B').sum()),n_C=int(g.evidence_tier.eq('C').sum())))
    return pd.DataFrame(result),rows


def figures(descriptive,coefficients,samples,out):
    out.mkdir(exist_ok=True,parents=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
    for ax,(tiers,_) in zip(axes,VERSIONS.items()):
        d=descriptive[descriptive.evidence_tiers.eq(tiers)].set_index('brand').reindex(BRANDS)
        ax.bar(BRANDS,d.mean_percentile,color=['#152c32','#547b82','#8ca9a1','#c5c9c3'])
        for i,(b,r) in enumerate(d.iterrows()):ax.text(i,r.mean_percentile+1,f'{r.mean_percentile:.1f}\nn={int(r.n_school_seasons)}',ha='center',fontsize=9)
        ax.set_title(f'{tiers} · covered priority cohort');ax.set_ylim(0,105);ax.tick_params(axis='x',rotation=12)
    axes[0].set_ylabel('Mean within-season performance percentile (0–100)')
    fig.suptitle('Nike schools score higher on average in the researched cohort',fontsize=15)
    fig.text(.5,.01,'n = school-seasons. Unadjusted, selected sample; association does not establish provider impact.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.94));fig.savefig(out/'brand_comparison.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,6),sharey=True)
    for ax,(tiers,_) in zip(axes,VERSIONS.items()):
        for offset,name,color in [(-.22,'plain','#a2a8a6'),(0,'plain_matched','#305966'),(.22,'lagged','#c17936')]:
            d=coefficients[(coefficients.evidence_tiers==tiers)&(coefficients.model==name)&coefficients.brand.isin(BRANDS[1:])].set_index('brand').reindex(BRANDS[1:])
            ys=np.arange(3)+offset
            ax.errorbar(d.coefficient,ys,xerr=np.vstack([d.coefficient-d.ci_low,d.ci_high-d.coefficient]),fmt='o',color=color,label=name.replace('_',' '),capsize=3)
        ax.axvline(0,color='#333',lw=.8);ax.set_yticks(np.arange(3),BRANDS[1:]);ax.set_title(tiers);ax.set_xlabel('Percentile-point difference versus Nike (95% CI)');ax.legend(fontsize=9)
        texts=[]
        for name in ['plain','lagged']:
            s=samples[(samples.evidence_tiers==tiers)&(samples.model==name)].set_index('brand')
            texts.append(name+': '+', '.join(f'{b} {int(s.loc[b,"n"])}' for b in BRANDS))
        ax.text(.0,-.21,'n school-seasons per brand\n'+'\n'.join(texts),transform=ax.transAxes,fontsize=8,va='top')
    fig.suptitle('Compare the same sample before and after controlling for prior performance',fontsize=14)
    fig.text(.5,.025,'Matched plain uses lagged sample counts. Lagged “other” is Boston College alone; do not generalize its interval.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.1,1,.95));fig.savefig(out/'controlled_models.png',dpi=160);plt.close(fig)


def analyze():
    reports=ROOT/'reports';out=reports/'figures'
    with duckdb.connect(str(ROOT/'data/processed/swoosh.duckdb'),read_only=True) as con:
        panel=prepare_panel(con.sql('SELECT * FROM analysis_panel').df())
        descriptive=con.sql((ROOT/'sql/descriptive_summaries.sql').read_text()).df()
        rowing,rowing_rows=rowing_summary(con,panel)
    coefficients,samples,diagnostics=fit_models(panel)
    share=shares(panel,pd.read_csv(ROOT/'data/sponsor_scope.csv'))
    tables={'brand_summary':descriptive,'model_coefficients':coefficients,'model_sample_sizes':samples,
        'model_diagnostics':diagnostics,'brand_shares':share,'rowing_summary':rowing,'rowing_scoring_rows':rowing_rows}
    for name,data in tables.items():data.to_csv(reports/f'{name}.csv',index=False)
    panel.to_csv(ROOT/'data/processed/analysis_panel.csv',index=False)
    figures(descriptive,coefficients,samples,out)
    from src.switch_cases import build_switch_cases
    cases=build_switch_cases(panel,ROOT)
    from src.phase3_report import write_report
    write_report(ROOT,tables,cases)
    summary=dict(status='Phase 3 complete; descriptive associations, not causal effects',evidence_versions=list(VERSIONS),
        primary_n=int(descriptive[descriptive.evidence_tiers=='A+B+C'].n_school_seasons.sum()),
        sensitivity_n=int(descriptive[descriptive.evidence_tiers=='A+B'].n_school_seasons.sum()),
        lag_rule='exact previous calendar season; 2019-20 excluded and never bridged',
        statsmodels_version=statsmodels.__version__,numpy_version=np.__version__,pandas_version=pd.__version__)
    (reports/'analysis_validation.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return tables


if __name__=='__main__':
    analyze()
