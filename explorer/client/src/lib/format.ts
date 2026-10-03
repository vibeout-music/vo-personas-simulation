// Small, pure formatting helpers shared by the components.

const regionNames = new Intl.DisplayNames(["en"], { type: "region" });
const languageNames = new Intl.DisplayNames(["en"], { type: "language" });

// "IT" -> "🇮🇹": each letter maps to a regional indicator symbol.
export function flag(countryCode: string): string {
  return String.fromCodePoint(...[...countryCode.toUpperCase()].map((c) => 0x1f1a5 + c.charCodeAt(0)));
}

export function countryName(code: string): string {
  return regionNames.of(code) ?? code;
}

export function languageName(code: string): string {
  if (code === "instrumental") return "Instrumental";
  return languageNames.of(code) ?? code;
}

// "early_career" -> "Early career"
export function humanize(value: string): string {
  const text = value.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

const GENRE_LABELS: Record<string, string> = {
  rnb: "R&B", kpop: "K-pop", jpop: "J-pop", khiphop: "K-hip hop", lofi: "Lo-fi", mpb: "MPB",
  drum_and_bass: "Drum & bass", edm: "EDM", hip_hop: "Hip-hop",
};

export function genreLabel(genre: string): string {
  return GENRE_LABELS[genre] ?? humanize(genre);
}

export function initials(name: string): string {
  return name.slice(0, 2).toUpperCase();
}

export function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

// Stable pastel color per persona, so each avatar keeps its color across renders.
export function avatarHue(id: string): number {
  let hash = 0;
  for (const char of id) hash = (hash * 31 + char.charCodeAt(0)) % 360;
  return hash;
}

// "2026-09-05T12:59+01:00" -> "Sat 12:59" (the persona's own local time, as written).
export function localTime(iso: string): string {
  const [date, time] = iso.split("T");
  const weekday = new Date(`${date}T00:00:00Z`).toLocaleDateString("en", { weekday: "short", timeZone: "UTC" });
  return `${weekday} ${time.slice(0, 5)}`;
}
