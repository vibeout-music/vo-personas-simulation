import { useEffect, useRef, type CSSProperties, type ReactNode } from "react";
import { usePersona } from "../hooks/usePersonas";
import { avatarHue, countryName, flag, genreLabel, humanize, initials, languageName, localTime, percent } from "../lib/format";
import type { PersonaDetail } from "../types/personaDetail";
import { Icon } from "./Icon";

interface PersonaDrawerProps {
  personaId: string | null;
  onClose: () => void;
}

export function PersonaDrawer({ personaId, onClose }: PersonaDrawerProps) {
  const state = usePersona(personaId);
  const closeRef = useRef<HTMLButtonElement>(null);
  const open = personaId !== null;

  // Escape closes the drawer; focus moves into it when it opens (keyboard and screen-reader users).
  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const onKeyDown = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  return (
    <>
      <div className={`scrim${open ? " open" : ""}`} onClick={onClose} aria-hidden="true" />
      <aside className={`drawer${open ? " open" : ""}`} role="dialog" aria-modal="true" aria-label="Persona details" inert={!open}>
        <div className="drawer-head">
          <span className="muted mono">{personaId}</span>
          <button ref={closeRef} type="button" className="icon-button" onClick={onClose} aria-label="Close details">
            <Icon name="close" />
          </button>
        </div>
        {open && state.status === "loading" && <DrawerSkeleton />}
        {open && state.status === "error" && <p className="empty error">Could not load this persona: {state.message}</p>}
        {open && state.status === "success" && <PersonaDetails persona={state.data.persona} />}
      </aside>
    </>
  );
}

function PersonaDetails({ persona: p }: { persona: PersonaDetail }) {
  const { demographics, residency, education, languages } = p.stable_profile;
  const { occupation } = p.work_and_occupation;
  const ctx = p.current_context;
  const intent = p.derived_listening_intent;
  const affect = p.mutable_state.current_affect;
  const body = p.mutable_state.physiological_state;
  const genres = Object.entries(p.music_identity.genres_and_styles.genre_affinities).sort(([, a], [, b]) => b - a);

  return (
    <div className="drawer-body">
      <div className="profile-head">
        <span className="avatar large" style={{ "--hue": avatarHue(p.metadata.persona_id) } as CSSProperties}>
          {initials(demographics.name_alias)}
        </span>
        <div>
          <h2>{demographics.name_alias}</h2>
          <p className="muted">
            {demographics.age} · {humanize(demographics.gender_identity)} · {flag(residency.country)} {countryName(residency.country)}
          </p>
          <div className="chips">
            <span className={`badge stage-${demographics.life_stage}`}>{humanize(demographics.life_stage)}</span>
            <span className="badge neutral">{humanize(p.platform_and_devices.tier)} plan</span>
          </div>
        </div>
      </div>

      <Section title="Right now" aside={<><Icon name="clock" size={13} /> {localTime(ctx.temporal.local_time)} local</>}>
        <p className="lead">
          {humanize(ctx.activity_and_location.activity)} at {ctx.activity_and_location.location_type.replaceAll("_", " ")},{" "}
          {ctx.social_context.social_company === "alone" ? "alone" : `with ${ctx.social_context.social_company}`} ·{" "}
          {humanize(ctx.environmental_conditions.weather.condition)}, {ctx.environmental_conditions.weather.temperature_c}°C
        </p>
        <Meter label="Mood" value={(affect.valence + 1) / 2} display={affect.valence.toFixed(2)} tone={affect.valence >= 0 ? "good" : "bad"} />
        <Meter label="Energy" value={body.energy} display={percent(body.energy)} />
        <Meter label="Stress" value={body.stress} display={percent(body.stress)} tone="bad" />
      </Section>

      <Section title="Listening intent">
        <Meter label="Likely to listen" value={intent.listen_probability} display={percent(intent.listen_probability)} tone="accent" />
        <dl className="facts">
          <Fact label="Music for">{humanize(intent.primary_function)}</Fact>
          <Fact label="Strategy">{humanize(intent.regulation_strategy)}</Fact>
          <Fact label="Device">{humanize(ctx.technical_setup.device)} · {ctx.technical_setup.audio_output.replaceAll("_", " ")}</Fact>
        </dl>
      </Section>

      <Section title="Profile">
        <dl className="facts">
          <Fact label="Occupation">{occupation.job_title ?? humanize(occupation.occupation)}</Fact>
          <Fact label="Status">{humanize(occupation.status)} · {humanize(occupation.work_environment)}</Fact>
          <Fact label="Education">
            {humanize(education.highest_completed)}
            {education.enrolled_in && ` · studying ${education.enrolled_in}`}
          </Fact>
          <Fact label="Home">{humanize(p.life_context.living_situation.living_arrangement)}</Fact>
          <Fact label="Relationship">{humanize(p.life_context.family_and_relationships.romantic_relationship.status)}</Fact>
          <Fact label="Languages">{languages.map((l) => languageName(l.code)).join(", ")}</Fact>
        </dl>
      </Section>

      <Section title="Personality" aside="Big Five">
        {Object.entries(p.psychology.big_five).map(([trait, value]) => (
          <Meter key={trait} label={humanize(trait)} value={value} display={percent(value)} />
        ))}
      </Section>

      <Section title="Music taste" aside={`Prefers ${p.music_identity.taste_profile.preferred_era}`}>
        <ul className="affinities">
          {genres.map(([genre, value]) => (
            <li key={genre}>
              <span>{genreLabel(genre)}</span>
              <span className="diverging" aria-label={`affinity ${value}`}>
                <span className={value >= 0 ? "pos" : "neg"} style={{ width: `${Math.abs(value) * 50}%` }} />
              </span>
              <span className="muted num">{value.toFixed(2)}</span>
            </li>
          ))}
        </ul>
        <dl className="facts">
          <Fact label="Grew up with">{p.music_identity.formative_exposure.map(genreLabel).join(", ")}</Fact>
          <Fact label="Listens in">{p.music_identity.listening_languages.map(languageName).join(", ")}</Fact>
        </dl>
      </Section>

      <Section title="Archetype">
        {Object.entries(p.metadata.archetype_mix).map(([name, weight]) => (
          <Meter key={name} label={humanize(name)} value={weight} display={percent(weight)} tone="accent" />
        ))}
      </Section>
    </div>
  );
}

function Section({ title, aside, children }: { title: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <section className="section">
      <header>
        <h3>{title}</h3>
        {aside && <span className="muted section-aside">{aside}</span>}
      </header>
      {children}
    </section>
  );
}

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="fact">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

interface MeterProps {
  label: string;
  value: number; // 0..1
  display: string;
  tone?: "neutral" | "good" | "bad" | "accent";
}

function Meter({ label, value, display, tone = "neutral" }: MeterProps) {
  return (
    <div className="meter">
      <span>{label}</span>
      <span className={`meter-track ${tone}`}>
        <span style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
      </span>
      <span className="muted num">{display}</span>
    </div>
  );
}

function DrawerSkeleton() {
  return (
    <div className="drawer-body" aria-busy="true">
      {Array.from({ length: 6 }, (_, i) => (
        <span key={i} className="skeleton block" />
      ))}
    </div>
  );
}
