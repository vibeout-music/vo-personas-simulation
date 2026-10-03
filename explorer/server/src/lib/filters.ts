import { isLifeStage, LIFE_STAGES, type LifeStage, type PersonaSummary } from "@/types/persona";

export interface PersonaFilters {
  country?: string;
  lifeStage?: LifeStage;
  limit?: number;
}

// Discriminated union: `ok` tells TypeScript which of the two shapes we have.
export type ParseResult =
  | { ok: true; filters: PersonaFilters }
  | { ok: false; error: string };

const MAX_LIMIT = 100;

// Query strings are untrusted input: everything arrives as string | null and must be validated.
export function parseFilters(params: URLSearchParams): ParseResult {
  const filters: PersonaFilters = {};

  const country = params.get("country");
  if (country !== null) {
    if (!/^[A-Za-z]{2}$/.test(country)) {
      return { ok: false, error: "country must be a two-letter code, e.g. IT" };
    }
    filters.country = country.toUpperCase();
  }

  const lifeStage = params.get("lifeStage");
  if (lifeStage !== null) {
    if (!isLifeStage(lifeStage)) {
      return { ok: false, error: `lifeStage must be one of: ${LIFE_STAGES.join(", ")}` };
    }
    filters.lifeStage = lifeStage; // narrowed to LifeStage by the type guard
  }

  const limit = params.get("limit");
  if (limit !== null) {
    const n = Number(limit);
    if (!Number.isInteger(n) || n < 1 || n > MAX_LIMIT) {
      return { ok: false, error: `limit must be an integer between 1 and ${MAX_LIMIT}` };
    }
    filters.limit = n;
  }

  return { ok: true, filters };
}

export function applyFilters(personas: PersonaSummary[], filters: PersonaFilters): PersonaSummary[] {
  const matching = personas.filter(
    (p) =>
      (filters.country === undefined || p.country === filters.country) &&
      (filters.lifeStage === undefined || p.lifeStage === filters.lifeStage),
  );
  return filters.limit === undefined ? matching : matching.slice(0, filters.limit);
}
