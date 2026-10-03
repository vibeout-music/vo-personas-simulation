// Inline SVG icons (no icon library). The name is a literal union, so typos fail to compile.
const PATHS = {
  home: "M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  users: "M16 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 17.5V19M10 10.5a3 3 0 1 0 0-6 3 3 0 0 0 0 6M20 19v-1.5a3.5 3.5 0 0 0-2.5-3.35M15.5 4.6a3 3 0 0 1 0 5.8",
  music: "M9 18V5l11-2v13M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0M20 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0",
  disc: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4",
  chart: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14M21 21l-4.35-4.35",
  close: "M18 6 6 18M6 6l12 12",
  help: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0",
  sortUp: "m7 14 5-5 5 5",
  sortDown: "m7 10 5 5 5-5",
  sortNone: "m8 9 4-4 4 4M16 15l-4 4-4-4",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M12 7v5l3 2",
} as const;

export type IconName = keyof typeof PATHS;

interface IconProps {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 16 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
