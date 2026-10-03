import type { LifeStage } from "../types/persona";

export interface PersonaQuery {
  country?: string;
  lifeStage?: LifeStage;
}

// URL builders: the hooks fetch, these only decide what to ask for.
export function personasUrl(query: PersonaQuery): string {
  const params = new URLSearchParams();
  if (query.country) params.set("country", query.country);
  if (query.lifeStage) params.set("lifeStage", query.lifeStage);
  const qs = params.toString();
  return `/api/personas${qs ? `?${qs}` : ""}`;
}

export function personaUrl(id: string): string {
  return `/api/personas/${encodeURIComponent(id)}`;
}
