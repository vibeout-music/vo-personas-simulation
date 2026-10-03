import type { LifeStage } from "./persona";

// The fields of a full persona that the detail drawer reads.
// The API sends ~270 fields; TypeScript is structural, so describing a subset is enough.
export interface PersonaDetail {
  metadata: { persona_id: string; archetype: string; archetype_mix: Record<string, number> };
  stable_profile: {
    demographics: { name_alias: string; age: number; birth_date: string; gender_identity: string; life_stage: LifeStage };
    residency: { country: string; timezone: string; environment: string };
    languages: { code: string; proficiency: number; is_primary: boolean }[];
    education: { highest_completed: string; enrolled_in: string | null };
  };
  psychology: { big_five: Record<"openness" | "conscientiousness" | "extraversion" | "agreeableness" | "neuroticism", number> };
  work_and_occupation: {
    occupation: { occupation: string; job_title: string | null; status: string; work_environment: string };
    schedule: { work_hours: [number, number] | null; weekly_hours: number };
  };
  life_context: {
    living_situation: { living_arrangement: string };
    family_and_relationships: { romantic_relationship: { status: string } };
  };
  music_identity: {
    genres_and_styles: { genre_affinities: Record<string, number> };
    taste_profile: { preferred_era: string };
    formative_exposure: string[];
    listening_languages: string[];
  };
  mutable_state: {
    current_affect: { valence: number; arousal: number };
    physiological_state: { stress: number; energy: number; sleep: { hours_last_night: number } };
  };
  current_context: {
    temporal: { local_time: string; day_type: string; time_of_day: string };
    activity_and_location: { activity: string; location_type: string };
    social_context: { social_company: string };
    technical_setup: { device: string; audio_output: string };
    environmental_conditions: { weather: { condition: string; temperature_c: number } };
  };
  derived_listening_intent: { listen_probability: number; primary_function: string; regulation_strategy: string };
  platform_and_devices: { tier: string };
}

export interface PersonaDetailResponse {
  persona: PersonaDetail;
}
