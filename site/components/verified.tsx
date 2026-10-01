import story from '@/data/story.json';
import charts from '@/data/charts.json';

type Entry = { text: string; raw: unknown; source: string; sample: string };
const registry = story.registry as Record<string, Entry>;

export function Stat({ name, className = '' }: { name: string; className?: string }) {
  const value = registry[name];
  if (!value) throw new Error(`Missing verified statistic: ${name}`);
  return <span className={className} data-number={name} title={`Source: ${value.source} · ${value.sample}`}>{value.text}</span>;
}

export function Chart({ name, label, className = '' }: { name: string; label: string; className?: string }) {
  const svg = (charts as Record<string, string>)[name];
  if (!svg) throw new Error(`Missing chart: ${name}`);
  return <div className={`chart ${className}`} role="img" aria-label={label}>
    <div className="chart-desktop" aria-hidden="true" data-plot={name} dangerouslySetInnerHTML={{ __html: svg }} />
    <div className="chart-mobile" aria-hidden="true" data-plot={`${name}-mobile`} dangerouslySetInnerHTML={{ __html: (charts as Record<string, string>)[`${name}-mobile`] }} />
  </div>;
}
