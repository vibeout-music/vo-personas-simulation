import { personasUrl, personaUrl, type PersonaQuery } from "../api/personas";
import type { PersonaListResponse } from "../types/persona";
import type { PersonaDetailResponse } from "../types/personaDetail";
import { useApi } from "./useApi";

// Thin, typed wrappers around the generic hook: components never build URLs or cast JSON.
export function usePersonas(query: PersonaQuery) {
  return useApi<PersonaListResponse>(personasUrl(query));
}

export function usePersona(id: string | null) {
  return useApi<PersonaDetailResponse>(id === null ? null : personaUrl(id));
}
