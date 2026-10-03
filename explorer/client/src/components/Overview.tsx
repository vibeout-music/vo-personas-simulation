import { useMemo } from "react";
import type { PersonaSummary } from "../types/persona";
import { countryName, flag, genreLabel, humanize, percent } from "../lib/format";

interface OverviewProps {
  personas: PersonaSummary[];
}

interface Row {
  label: string;
  value: number;
}

function countBy(values: string[]): Row[] {
  const counts = new Map<string, number>();
  for (const v of values) counts.set(v, (counts.get(v) ?? 0) + 1);
  return [...counts.entries()].map(([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value);
}

function median(numbers: number[]): number {
  if (numbers.length === 0) return 0;
  const sorted = [...numbers].sort((a, b) => a - b); // copy first: sort() mutates
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : Math.round((sorted[mid - 1] + sorted[mid]) / 2);
}

export function Overview({ personas }: OverviewProps) {
  // Derived data: recomputed only when the list changes, not on every render.
  const stats = useMemo(() => {
    const countries = countBy(personas.map((p) => p.country));
    const genres = countBy(personas.flatMap((p) => p.topGenres));
    return {
      total: personas.length,
      countries,
      medianAge: median(personas.map((p) => p.age)),
      employed: personas.length ? personas.filter((p) => p.jobTitle !== null).length / personas.length : 0,
      stages: countBy(personas.map((p) => p.lifeStage)),
      genres,
    };
  }, [personas]);

  return (
    <section className="overview" aria-label="Overview">
      <div className="stats">
        <Stat label="Personas" value={String(stats.total)} hint="matching filters" />
        <Stat label="Countries" value={String(stats.countries.length)} hint={stats.countries[0] ? `most: ${countryName(stats.countries[0].label)}` : "—"} />
        <Stat label="Median age" value={stats.total ? String(stats.medianAge) : "—"} hint="years" />
        <Stat label="Working" value={stats.total ? percent(stats.employed) : "—"} hint="have a job title" />
      </div>
      <div className="breakdowns">
        <Breakdown title="Life stage" rows={stats.stages} total={stats.total} format={humanize} />
        <Breakdown title="Top countries" rows={stats.countries.slice(0, 5)} total={stats.total} format={(c) => `${flag(c)}  ${countryName(c)}`} />
        <Breakdown title="Favourite genres" rows={stats.genres.slice(0, 5)} total={stats.total} format={genreLabel} />
      </div>
    </section>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="card stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      <span className="stat-hint">{hint}</span>
    </div>
  );
}

interface BreakdownProps {
  title: string;
  rows: Row[];
  total: number;
  format: (label: string) => string;
}

function Breakdown({ title, rows, total, format }: BreakdownProps) {
  return (
    <div className="card breakdown">
      <h3>{title}</h3>
      {rows.length === 0 && <p className="muted">No data</p>}
      <ul>
        {rows.map((row) => (
          <li key={row.label}>
            <div className="breakdown-row">
              <span>{format(row.label)}</span>
              <span className="muted">{row.value}</span>
            </div>
            <div className="bar">
              <span style={{ width: `${total ? (row.value / total) * 100 : 0}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
