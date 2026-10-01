"""Generate personas in causal order and write them as JSONL."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

from .draft import Draft
from .rules import load_template, validate
from .sampling import derive_seed, r2
from .moment import apply_moment
from .sections import behavior, emotional, environment, identity, life, music, psychology, work
from .tables import ARCHETYPES


class IncoherentPersona(ValueError):
    pass


def sample_archetypes(rng: random.Random) -> tuple[str, dict]:
    """Each persona is a mixture of one or two archetypes, not a clone of one."""
    primary = rng.choice(ARCHETYPES)
    if rng.random() < 0.6:
        secondary = rng.choice([a for a in ARCHETYPES if a != primary])
        w = r2(rng.uniform(0.2, 0.45))
        return primary, {primary: r2(1 - w), secondary: w}
    return primary, {primary: 1.0}


def generate_persona(index: int, simulation_seed: int, reference: datetime) -> dict:
    persona_seed = derive_seed(simulation_seed, index)
    rng = random.Random(persona_seed)
    # Snapshot instants are spread over the week after the reference date so the
    # population covers every hour, weekdays and weekends.
    d = Draft(rng=rng, when=reference + timedelta(seconds=rng.randrange(7 * 24 * 3600)))
    primary, mix = sample_archetypes(rng)
    d.facts["archetype_mix"] = mix

    # Causal order: each step only reads what earlier steps produced.
    identity.build(d)          # country, age, education
    psychology.build_core(d)   # personality
    work.build(d)              # status, occupation, schedule, income, commute, exercise
    life.build(d)              # relationships, household, social, health, money, life events, sleep
    psychology.build_goals(d)  # goals depend on work and family
    emotional.build(d)
    music.build(d)
    behavior.build(d)
    environment.build_environment(d)
    environment.build_platform(d)
    # The snapshot moment goes through the same code path as any later moment.
    apply_moment(d.persona, d.when, derive_seed(persona_seed, "moment"))
    d.persona["memory_references"] = {"person_track_state": [], "person_artist_state": [], "recent_listening_events": []}

    number = index + 1
    p = d.persona
    persona = {
        "metadata": {
            "id": f"p_{number:06d}",
            "persona_id": f"persona_{number:06d}",
            "schema_version": load_template()["metadata"]["schema_version"],
            "seed": persona_seed,
            "simulation_seed": simulation_seed,
            "archetype": primary,
            "archetype_mix": mix,
            "$schema": None,
            "_llm_model": None,
        }
    }
    # Emit sections in the schema's order.
    for key in load_template():
        if key != "metadata":
            persona[key] = p[key]
    return persona


def generate_population(count: int, seed: int, reference: datetime) -> Iterator[dict]:
    for i in range(count):
        persona = generate_persona(i, seed, reference)
        errors = validate(persona)
        if errors:
            raise IncoherentPersona(f"{persona['metadata']['persona_id']}: " + "; ".join(errors))
        yield persona


def write_jsonl(personas, out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for persona in personas:
            fh.write(json.dumps(persona, ensure_ascii=False, separators=(",", ":")) + "\n")
            n += 1
    return n
