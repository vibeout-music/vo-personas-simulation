import { useMemo, useState, type CSSProperties } from "react";
import type { ApiState } from "../hooks/useApi";
import { avatarHue, countryName, flag, genreLabel, humanize, initials } from "../lib/format";
import type { PersonaListResponse, PersonaSummary } from "../types/persona";
import { Icon } from "./Icon";

type SortKey = "alias" | "age" | "country" | "lifeStage";
type SortDir = "asc" | "desc";

interface PersonaTableProps {
  state: ApiState<PersonaListResponse>;
  personas: PersonaSummary[]; // already searched by the parent
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const COLUMNS: { key: SortKey | null; label: string; className?: string }[] = [
  { key: "alias", label: "Persona" },
  { key: "age", label: "Age", className: "num" },
  { key: "country", label: "Country" },
  { key: "lifeStage", label: "Life stage" },
  { key: null, label: "Occupation" },
  { key: null, label: "Top genres" },
];

export function PersonaTable({ state, personas, selectedId, onSelect }: PersonaTableProps) {
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir }>({ key: "alias", dir: "asc" });

  // Sorting is derived from props + state: memoized so it only re-runs when they change.
  const rows = useMemo(() => {
    const factor = sort.dir === "asc" ? 1 : -1;
    return [...personas].sort((a, b) => {
      const x = a[sort.key];
      const y = b[sort.key];
      return (typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y))) * factor;
    });
  }, [personas, sort]);

  function toggleSort(key: SortKey) {
    setSort((prev) => ({ key, dir: prev.key === key && prev.dir === "asc" ? "desc" : "asc" }));
  }

  return (
    <div className="card table-card">
      <table className="table">
        <thead>
          <tr>
            {COLUMNS.map(({ key, label, className }) => (
              <th key={label} className={className} aria-sort={key && sort.key === key ? (sort.dir === "asc" ? "ascending" : "descending") : undefined}>
                {key ? (
                  // `key` is narrowed to SortKey here, and the closure keeps that narrowing.
                  <button type="button" className="sort" onClick={() => toggleSort(key)}>
                    {label}
                    <Icon name={sort.key !== key ? "sortNone" : sort.dir === "asc" ? "sortUp" : "sortDown"} size={12} />
                  </button>
                ) : (
                  label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {state.status === "loading" &&
            Array.from({ length: 8 }, (_, i) => (
              <tr key={i} className="skeleton-row" aria-hidden="true">
                {COLUMNS.map((col) => (
                  <td key={col.label}><span className="skeleton" /></td>
                ))}
              </tr>
            ))}

          {state.status === "error" && (
            <tr>
              <td colSpan={COLUMNS.length} className="empty error">Could not load personas: {state.message}</td>
            </tr>
          )}

          {state.status === "success" && rows.length === 0 && (
            <tr>
              <td colSpan={COLUMNS.length} className="empty">No personas match these filters.</td>
            </tr>
          )}

          {state.status === "success" &&
            rows.map((p) => (
              <tr
                key={p.id}
                className={`row${p.id === selectedId ? " selected" : ""}`}
                tabIndex={0}
                onClick={() => onSelect(p.id)}
                onKeyDown={(e) => e.key === "Enter" && onSelect(p.id)}
              >
                <td>
                  <div className="persona-cell">
                    <span className="avatar" style={{ "--hue": avatarHue(p.id) } as CSSProperties}>{initials(p.alias)}</span>
                    <div>
                      <div className="strong">{p.alias}</div>
                      <div className="muted mono">{p.id}</div>
                    </div>
                  </div>
                </td>
                <td className="num">{p.age}</td>
                <td>
                  <span title={countryName(p.country)}>{flag(p.country)} {p.country}</span>
                </td>
                <td>
                  <span className={`badge stage-${p.lifeStage}`}>{humanize(p.lifeStage)}</span>
                </td>
                <td>
                  <div>{p.jobTitle ?? humanize(p.occupation)}</div>
                </td>
                <td>
                  <div className="chips">
                    {p.topGenres.map((g) => (
                      <span key={g} className="chip">{genreLabel(g)}</span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
