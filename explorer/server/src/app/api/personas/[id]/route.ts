import type { RawPersona } from "@/types/persona";
import { loadPersonas } from "@/lib/personas";

// Shape of the response body, so the client can share the same contract.
export interface PersonaResponse {
  persona: RawPersona;
}

// GET /api/personas/[id]
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;

  const personas = await loadPersonas();
  const result = personas.find((p) => p.metadata.persona_id === id); // RawPersona | undefined

  if (!result) {
    return Response.json({ error: "Persona not found" }, { status: 404 });
  }

  // Narrowed: TypeScript now knows `result` is RawPersona.
  const body: PersonaResponse = { persona: result };
  return Response.json(body);
}
