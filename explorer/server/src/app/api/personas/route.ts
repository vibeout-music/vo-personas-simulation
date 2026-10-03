import type { PersonaSummary } from "@/types/persona";
import { loadPersonas, toSummary } from "@/lib/personas";
import { applyFilters, parseFilters } from "@/lib/filters";

// Shape of the response body, so the client can share the same contract.
export interface PersonaListResponse {
  count: number;
  personas: PersonaSummary[];
}

// GET /api/personas?country=IT&lifeStage=senior&limit=10
export async function GET(request: Request): Promise<Response> {
  const parsed = parseFilters(new URL(request.url).searchParams);
  if (!parsed.ok) {
    // Narrowed by the discriminant: here `parsed` is { ok: false; error: string }.
    return Response.json({ error: parsed.error }, { status: 400 });
  }

  const raw = await loadPersonas();
  const personas = applyFilters(raw.map(toSummary), parsed.filters);

  const body: PersonaListResponse = { count: personas.length, personas };
  return Response.json(body);
}
