import { readFile } from "node:fs/promises";
import path from "node:path";
import type { PersonaSummary, RawPersona } from "@/types/persona";

const DATA_PATH =
  process.env.PERSONAS_PATH ??
  path.join(process.cwd(), "..", "..", "data", "fixtures", "personas_fixture.jsonl");

let cache: RawPersona[] | null = null;

export async function loadPersonas(): Promise<RawPersona[]> {
  if (cache) return cache;
  const text = await readFile(DATA_PATH, "utf-8");
  cache = text
    .split("\n")
    .filter((line) => line.trim() !== "")
    .map((line) => JSON.parse(line) as RawPersona);
  return cache;
}

// Maps the nested, snake_case persona on disk to the flat, camelCase shape the API returns.
export function toSummary(raw: RawPersona): PersonaSummary {
  const { demographics, residency } = raw.stable_profile;
  const { occupation } = raw.work_and_occupation;

  const topGenres = Object.entries(raw.music_identity.genres_and_styles.genre_affinities)
    .sort(([, a], [, b]) => b - a) // highest affinity first
    .slice(0, 3)
    .map(([genre]) => genre);

  return {
    id: raw.metadata.persona_id,
    alias: demographics.name_alias,
    age: demographics.age,
    country: residency.country,
    lifeStage: demographics.life_stage,
    occupation: occupation.occupation,
    jobTitle: occupation.job_title,
    topGenres,
    archetype: raw.metadata.archetype,
  };
}