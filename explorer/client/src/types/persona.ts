// Types use PascalCase; properties use camelCase.

// Single source of truth: a runtime array (for validation) and a type derived from it.
export const LIFE_STAGES = ["teenager", "young_adult", "early_career", "established_adult", "midlife", "senior"] as const;
export type LifeStage = (typeof LIFE_STAGES)[number];

// Type guard: if it returns true, TypeScript narrows `value` to LifeStage.
export function isLifeStage(value: string): value is LifeStage {
  return (LIFE_STAGES as readonly string[]).includes(value);
}

// A lightweight view of a persona, for lists. The full persona has ~270 fields.
export interface PersonaSummary {
  id: string;
  alias: string;
  age: number;
  country: string;
  lifeStage: LifeStage;
  occupation: string;
  jobTitle: string | null;
  topGenres: string[];
  archetype: string;
}

// Shape of a persona on disk: only the fields we read (TypeScript is structural).
export interface RawPersona {
  metadata: { persona_id: string; archetype: string };
  stable_profile: {
    demographics: { name_alias: string; age: number; life_stage: LifeStage };
    residency: { country: string };
  };
  work_and_occupation: { occupation: { occupation: string; job_title: string | null } };
  music_identity: { genres_and_styles: { genre_affinities: Record<string, number> } };
}

// Response contracts of the API (same shapes as the server's route handlers).
export interface PersonaListResponse {
  count: number;
  personas: PersonaSummary[];
}

export interface ApiErrorBody {
  error: string;
}
