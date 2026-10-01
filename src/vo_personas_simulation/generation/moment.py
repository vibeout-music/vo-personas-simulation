"""Recompute the moment of a persona -- context, latent state and listening intent -- for any instant.

The stable parts of a persona (identity, psychology, work, taste...) never
change here. Only what depends on the instant is rebuilt: age-derived fields
(people have birthdays), current_context, mutable_state and
derived_listening_intent. The generator uses this same function for the
snapshot it writes, so a generated persona and a recomputed moment can never
disagree.
"""

from __future__ import annotations

import copy
import random
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .draft import Draft, age_on, facts_from_persona, life_stage_for
from .sections import context, intent, state


def apply_moment(persona: dict, when: datetime, seed: int) -> dict:
    """Rebuild the moment in place and return the persona."""
    sp = persona["stable_profile"]
    local = when.astimezone(ZoneInfo(sp["residency"]["timezone"]))
    birth = date.fromisoformat(sp["demographics"]["birth_date"])
    age = age_on(birth, local.date())
    sp["demographics"]["age"] = age
    sp["demographics"]["life_stage"] = life_stage_for(age)
    sp["formative_music_years"] = [birth.year + 12, min(birth.year + 22, local.year)]

    d = Draft(rng=random.Random(seed), when=when, persona=persona, local=local,
              facts=facts_from_persona(persona, local.date()))
    context.build(d)
    state.build(d)
    intent.build(d)
    return persona


def build_moment(persona: dict, when: datetime, seed: int) -> dict:
    """A copy of the persona living the given instant."""
    return apply_moment(copy.deepcopy(persona), when, seed)
