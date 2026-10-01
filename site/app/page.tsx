import Image from 'next/image';
import story from '@/data/story.json';
import personal from '@/content/personal.json';
import image from '@/data/image.json';
import { Chart, Stat } from '@/components/verified';
import { Reveal } from '@/components/reveal';

function SectionHead({ index, eyebrow, title, id }: { index: string; eyebrow: string; title: string; id: string }) {
  return <div className="section-head" data-reveal>
    <span className="section-number" data-decoration="section" aria-hidden="true">{index}</span>
    <div><p className="eyebrow">{eyebrow}</p><h2 id={id}>{title}</h2></div>
  </div>;
}
function Source({ path, label = 'View the source data' }: { path: string; label?: string }) {
  return <a className="source-link" href={`${story.links.github}/blob/main/${path}`}>{label} <span aria-hidden="true">↗</span></a>;
}
function CaseChart({ item, index }: { item: typeof story.cases[number]; index: number }) {
  return <article className="case-card" data-reveal>
    <div className="case-heading"><h3>{item.school}</h3><span className="case-year"><Stat name={`case.${index}.season`} /></span></div>
    <p className="case-provider">{item.from} <span aria-hidden="true">→</span><span className="sr-only"> to </span> {item.to}</p>
    <Chart name={`case-${index}`} label={`${item.school}: performance percentile before and after the provider switch. Missing annual outcomes appear as gaps. Switch season is marked by the vertical dashed line.`} />
    <p className="case-note"><Stat name={`case.${index}.shortNote`} /></p>
    <details><summary>Context and chart values</summary>
      <p className="detail-note"><Stat name={`case.${index}.note`} /></p>
      <div className="table-wrap"><table><caption className="sr-only">{item.school} case-study values</caption><thead><tr><th scope="col">Season</th><th scope="col">Relative</th><th scope="col">Percentile</th></tr></thead><tbody>{item.points.map((point, j) => <tr key={point.relative}><th scope="row"><Stat name={`case.${index}.${j}.season`} /></th><td><Stat name={`case.${index}.${j}.relative`} /></td><td><Stat name={`case.${index}.${j}.value`} /></td></tr>)}</tbody></table></div>
      <div className="context-links">{item.coachingSource && <a href={item.coachingSource}>Coaching source ↗</a>}{item.realignmentSource && <a href={item.realignmentSource}>Conference source ↗</a>}</div>
    </details>
  </article>;
}

export default function Home() {
  return <>
    <a className="skip-link" href="#findings">Skip to the findings</a>
    <main>
      <section className="hero dark" aria-labelledby="hero-title">
        <div className="hero-content">
          <div className="hero-top"><a className="project-label" href="#hero-title">THE SWOOSH EFFECT</a><span className="edition" data-decoration="section">01 / A PERSONAL DATA STORY</span></div>
          <h1 id="hero-title"><span>I ONLY WANTED</span><span>TO ROW FOR A</span><span className="orange">NIKE SCHOOL.</span></h1>
          <p className="hero-subhead"><Stat name="copy.subhead" /></p>
          <div className="hero-bottom"><p className="byline">By <a href={story.links.linkedin}>Alexandra Cowan</a></p><a className="scroll-cue" href="#findings">FOLLOW THE DATA <span aria-hidden="true">↓</span></a></div>
        </div>
      </section>

      <section className="section light" id="findings" aria-labelledby="rates-title">
        <div className="container"><SectionHead index="02" eyebrow="The pattern" title="The best programs wear Nike" id="rates-title" />
          <div className="rates-grid" data-reveal>
            <div className="stat-panel"><div className="stat-stage dark"><Stat name="brand.0.rate" className="big-stat orange" /><span className="stat-caption" data-definition="top10">NIKE’S TOP-10 FINISH RATE</span></div><p className="stat-support"><Stat name="brand.0.finishes" /> <span data-definition="top10">top-10</span> finishes in <Stat name="brand.0.n" /> Nike school-seasons.</p></div>
            <figure className="rates-figure"><Chart name="rates" label="Top-10 finish rates within each provider’s directly evidenced school-seasons. Nike has the highest rate. Exact rates and counts are listed below." />
              <div className="rate-labels">{story.brands.map((brand, i) => <div key={brand.brand}><span className={`swatch ${i === 0 ? 'swatch-nike' : i === 1 ? 'swatch-ua' : 'swatch-adidas'}`} /><strong>{brand.brand}</strong><span><Stat name={`brand.${i}.rate`} /> · n = <Stat name={`brand.${i}.n`} /></span></div>)}</div>
              <figcaption>Rates are within each brand’s covered school-seasons, not national market share.</figcaption>
            </figure>
          </div>
          <div className="section-foot"><p>A+B = seasons with direct sponsor evidence. Department-level performance across NCAA sports.</p><Source path="reports/brand_summary.csv" /></div>
          <details className="readme-copy"><summary>Read the finding and sample definition</summary><p><Stat name="copy.brand" /></p></details>
        </div>
      </section>

      <section className="section dark" aria-labelledby="pick-title">
        <div className="container"><SectionHead index="03" eyebrow="The harder question" title="Pick or make?" id="pick-title" />
          <div className="takeaway takeaway-lead" data-reveal><div><span className="eyebrow">AFTER ACCOUNTING FOR LAST SEASON</span><span className="takeaway-stat orange"><Stat name="comparison.shrinkRange" /></span><span className="takeaway-word">SMALLER</span></div><p>Consistent with Nike signing already-strong programs, not proof that Nike makes them better.</p></div>
          <p className="chart-note">Before and after: adjusted Nike advantages on the same matched A+B school-seasons, with conference and season controls.</p>
          <div className="comparison-grid">{story.comparisons.map((d, i) => <figure key={d.brand} data-reveal><div className="figure-heading"><h3>Nike vs {d.brand}</h3><span className="reduction"><Stat name={`comparison.${i}.shrinkage`} /> smaller</span></div><Chart name={`comparison-${i}`} label={`Nike advantage over ${d.brand}, comparing the conference- and season-adjusted model before and after including last season’s performance. Whiskers are 95% confidence intervals and include zero.`} />
            <figcaption className="coefficient-values">{d.estimates.map((e, j) => <span key={e.model}>{e.label}: <strong><Stat name={`comparison.${i}.${j}.estimate`} /></strong> [<Stat name={`comparison.${i}.${j}.low`} />, <Stat name={`comparison.${i}.${j}.high`} />]</span>)}</figcaption></figure>)}</div>
          <div className="section-foot"><p>A+B · matched n = <Stat name="comparison.n" /> · conference and season controls · <Stat name="confidence" /> CIs clustered by school. All major-brand intervals include zero.</p><Source path="reports/model_coefficients.csv" label="Model estimates and intervals" /></div>
          <details className="readme-copy"><summary>Sample counts and the README finding</summary><p>Unadjusted A+B mean-percentile leads: +<Stat name="comparison.0.raw" /> over adidas and +<Stat name="comparison.1.raw" /> over Under Armour.</p><p>Unadjusted means compare observed brand averages; adjusted estimates control for conference and season, then add prior-season performance on the same matched rows.</p><p>Adjusted matched sample: <Stat name="comparison.perBrand" />.</p><p><Stat name="copy.pick" /></p></details>
        </div>
      </section>

      <section className="section light" aria-labelledby="ml-title">
        <div className="container"><SectionHead index="04" eyebrow="A forecasting reality check" title="Can a model predict it?" id="ml-title" />
          <div className="ml-grid" data-reveal><div><p className="lead">The toughest benchmark?<br /><strong>Same as last season.</strong></p><p className="body-copy">Forecast the next season using only earlier information. Train on earlier seasons; hold out <Stat name="ml.testSeasons" />. Compare all models on the same <Stat name="ml.n" /> school-seasons.</p>
            <table className="mae-table"><caption>Mean absolute error · lower is better</caption><thead><tr><th scope="col">Model</th><th scope="col">MAE</th><th scope="col"><Stat name="confidence" /> CI</th></tr></thead><tbody>{story.ml.models.map((m, i) => <tr key={m.model} className={i === 0 ? 'baseline-row' : ''}><th scope="row">{m.label}</th><td><Stat name={`ml.${i}.mae`} /></td><td><Stat name={`ml.${i}.low`} />–<Stat name={`ml.${i}.high`} /></td></tr>)}</tbody></table>
            <p className="body-copy">No model clearly beat the last-season baseline on MAE. OLS and LightGBM did improve RMSE, so the result depends on how error is measured.</p>
          </div><figure><div className="figure-heading"><h3>What the model relies on</h3><span className="small-label">PERMUTATION IMPORTANCE</span></div><Chart name="importance" label="Ten most important LightGBM features. Last season’s percentile ranks first. Bars show the increase in held-out mean absolute error when each feature is shuffled within season, on a symmetric log scale." /><figcaption>Last season is the #<Stat name="feature.0.rank" /> predictor of <Stat name="ml.featureCount" /> inputs. Symmetric log scale makes the small contributions visible.</figcaption>
            <details><summary>Exact feature values</summary><table><caption className="sr-only">Top feature importance, MAE increase</caption><thead><tr><th scope="col">Feature</th><th scope="col">Rank</th><th scope="col">MAE increase</th></tr></thead><tbody>{story.ml.features.map((f, i) => <tr key={f.feature}><th scope="row">{f.label}</th><td><Stat name={`feature.${i}.rank`} /></td><td><Stat name={`feature.${i}.importance`} /></td></tr>)}</tbody></table></details>
          </figure></div>
          <aside className="caveat"><strong>What about brand?</strong><p>Brand’s measured importance was <Stat name="ml.brandImportance" /> in this benchmark, but <Stat name="ml.masked" /> of <Stat name="ml.n" /> holdout rows had masked or unknown brand. Only <Stat name="ml.known" /> had dated pre-season assignments. This cannot establish that brands have no effect.</p></aside>
          <div className="section-foot"><p>Time-based validation, rolling-origin tuning and school-clustered bootstrap intervals. No same-season performance enters the predictors.</p><Source path="reports/ml/metrics.csv" label="Forecast results" /></div>
          <details className="readme-copy"><summary>RMSE values and the README finding</summary><p><Stat name="copy.ml" /></p><p>RMSE: baseline <Stat name="ml.0.rmse" />; OLS <Stat name="ml.1.rmse" />; LightGBM <Stat name="ml.2.rmse" />.</p></details>
        </div>
      </section>

      <section className="section dark" aria-labelledby="switch-title">
        <div className="container"><SectionHead index="05" eyebrow="Supporting evidence" title="Schools that switched" id="switch-title" />
          <div className="switch-intro"><p className="lead">New provider.<br />A lot else changed, too.</p><p className="body-copy"><Stat name="cases.n" /> usable cases from <Stat name="cases.documented" /> documented transitions. These are descriptive histories, not causal experiments. The dashed line is the switch season; orange marks Nike observations.</p></div>
          <div className="switch-grid">{story.cases.map((item, i) => <CaseChart key={item.school} item={item} index={i} />)}</div>
          <div className="section-foot"><p>A+B observed outcomes · calendar seasons retained · the cancelled <Stat name="cases.cancelledSeason" /> annual final stays a gap. {story.excluded.join(', ')} is excluded because pre-switch provider evidence is insufficient.</p><Source path="reports/switch_case_confounders.csv" label="Read the confounder screen" /></div>
          <p className="body-copy switch-caution">Cincinnati’s dip coincides with its conference move and a football coaching change. Coaching checks cover selected football and basketball leadership; an unlisted change does not mean every staff was stable.</p>
        </div>
      </section>

      <section className="section dark personal" aria-labelledby="why-title">
        <div className="container"><SectionHead index="06" eyebrow="The person behind the question" title="Why Nike" id="why-title" />
          <div className="personal-grid" data-reveal>
            <figure className="commit-figure">
              <picture>
                <source type="image/avif" srcSet={image.variants.filter(d => d.format === 'avif').map(d => `${d.src} ${d.width}w`).join(', ')} sizes="(max-width: 740px) calc(100vw - 48px), (max-width: 1050px) 42vw, 460px" />
                <source type="image/webp" srcSet={image.variants.filter(d => d.format === 'webp').map(d => `${d.src} ${d.width}w`).join(', ')} sizes="(max-width: 740px) calc(100vw - 48px), (max-width: 1050px) 42vw, 460px" />
                <Image src={image.original.src} width={image.original.width} height={image.original.height} alt={personal.alt} className="commit-image" loading="lazy" unoptimized />
              </picture>
              <figcaption>{personal.caption}</figcaption>
            </figure>
            <div className="personal-copy"><p className="personal-story">{personal.paragraph}</p><blockquote><p>“IF YOU HAVE A BODY,<br />YOU ARE AN ATHLETE.”</p><footer>— Bill Bowerman, Nike co-founder.<br /><a href={story.links.quote}>Quote wording ↗</a> · <a href={story.links.attribution}>Attribution ↗</a></footer></blockquote></div>
          </div>
        </div>
      </section>

      <section className="section dark" aria-labelledby="build-title">
        <div className="container"><SectionHead index="07" eyebrow="From a personal hunch to a reproducible project" title="How I built it" id="build-title" />
          <ol className="pipeline" aria-label="Project pipeline" data-reveal>{[['INPUT', 'Directors’ Cup PDFs'], ['EXTRACT', 'Python parser'], ['ORGANIZE', 'DuckDB / SQL'], ['TEST', 'OLS + LightGBM'], ['SHARE', 'Tableau / site']].map(([label, title]) => <li key={label}><span className="eyebrow">{label}</span><strong>{title}</strong></li>)}</ol>
          <div className="tech-chips" aria-label="Technology stack">{['Python', 'SQL', 'DuckDB', 'LightGBM', 'statsmodels', 'pytest', 'GitHub Actions', 'Docker', 'Tableau', 'Next.js', 'TypeScript', 'Tailwind', 'Observable Plot'].map(item => <span key={item}>{item}</span>)}</div>
          <div className="method-grid" data-reveal><div><h3>Evidence before conclusions.</h3><dl className="tiers"><div><dt>A</dt><dd>Contract, board record or announcement. Reported contract terms retain their source label.</dd><dd className="tier-count"><Stat name="coverage.A" /> seasons</dd></div><div><dt>B</dt><dd>Dated official evidence of the provider in use that season, including archived athletics pages.</dd><dd className="tier-count"><Stat name="coverage.B" /> seasons</dd></div><div><dt>C</dt><dd>Inferred continuity only between the same directly verified provider, with no intervening switch.</dd><dd className="tier-count"><Stat name="coverage.C" /> seasons</dd></div></dl><p className="body-copy">Headlines use A+B. A+B+C is reported separately. Unknown providers stay unknown; team exceptions are documented without being modeled.</p></div><div className="coverage-panel"><Stat name="coverage.rate" className="coverage-stat orange" /><p>Coverage of the <Stat name="coverage.schools" />-school research scope</p><p className="small-copy"><Stat name="coverage.covered" /> / <Stat name="coverage.total" /> school-seasons covered by A+B+C. <Stat name="coverage.unknown" /> remain unverified.</p></div></div>
          <div className="limitations"><h3>Where the evidence stops</h3><ul><li>This is a selected department cohort, not a census of Division I or a measure of brand market share.</li><li>Observational comparisons cannot separate provider effects from budgets, sport offerings, recruiting or prior performance.</li><li>COVID, conference moves and coaching changes complicate switch histories. Payment disputes do not change provider assignments.</li><li>Strict pre-season dating masks many ML brand inputs. Historical source revisions and incomplete sponsor evidence limit interpretation.</li></ul><a className="source-link" href={story.links.methodology}>Full methodology, samples and limitations ↗</a> <a className="source-link" href={story.links.sources}>Data sources and evidence ↗</a></div>
          <div className="outro" data-reveal><p className="display outro-title">EXPLORE THE EVIDENCE.</p><div className="button-row"><a className="button button-primary" href={story.links.github}>GitHub repo <span aria-hidden="true">↗</span></a><a className="button" href={story.links.tableau}>Tableau dashboard <span aria-hidden="true">↗</span></a><a className="button" href={story.links.linkedin}>LinkedIn <span aria-hidden="true">↗</span></a></div></div>
        </div>
      </section>
    </main>
    <footer className="site-footer dark"><p>Independent student project by Alexandra Cowan. Not affiliated with or endorsed by Nike, Inc.</p><a href="#hero-title">BACK TO TOP ↑</a></footer>
    <Reveal />
  </>;
}
