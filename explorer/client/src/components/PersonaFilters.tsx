import type { PersonaQuery } from "../api/personas";
import { countryName, flag, humanize } from "../lib/format";
import { isLifeStage, LIFE_STAGES } from "../types/persona";

const COUNTRIES = ["AR", "AU", "BR", "CO", "DE", "ES", "FR", "GB", "IN", "IT", "JP", "KR", "MX", "NG", "US"];

interface PersonaFiltersProps {
  value: PersonaQuery;
  onChange: (next: PersonaQuery) => void; // the parent owns the state ("lifting state up")
  resultCount: number | null;
}

// Controlled component: what the controls show always comes from props, never from the DOM.
export function PersonaFilters({ value, onChange, resultCount }: PersonaFiltersProps) {
  const tabs = ["all", ...LIFE_STAGES] as const;

  return (
    <div className="toolbar">
      <div className="tabs" role="tablist" aria-label="Life stage">
        {tabs.map((tab) => {
          const selected = tab === "all" ? value.lifeStage === undefined : value.lifeStage === tab;
          return (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={selected}
              className={`tab${selected ? " selected" : ""}`}
              onClick={() => onChange({ ...value, lifeStage: isLifeStage(tab) ? tab : undefined })}
            >
              {tab === "all" ? "All" : humanize(tab)}
            </button>
          );
        })}
      </div>

      <div className="toolbar-right">
        {resultCount !== null && <span className="muted">{resultCount} results</span>}
        <select
          className="select"
          aria-label="Country"
          value={value.country ?? ""}
          onChange={(e) => onChange({ ...value, country: e.target.value || undefined })}
        >
          <option value="">All countries</option>
          {COUNTRIES.map((code) => (
            <option key={code} value={code}>
              {flag(code)} {countryName(code)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
