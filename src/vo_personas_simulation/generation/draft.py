"""State shared by the section builders while one persona is generated."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Draft:
    rng: random.Random
    when: datetime                     # snapshot instant (UTC)
    persona: dict = field(default_factory=dict)
    local: datetime | None = None      # snapshot instant in the persona's timezone
    # Facts that drive later sections but are not persona fields.
    facts: dict = field(default_factory=dict)

    def get(self, path: str):
        node = self.persona
        for key in path.split("."):
            node = node[key]
        return node


def age_on(birth: date, day: date) -> int:
    return day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))


def life_stage_for(age: int) -> str:
    from .tables import LIFE_STAGES

    return next(label for label, lo, hi in LIFE_STAGES if lo <= age <= hi)


WORKING_STATUSES = ("employed", "self_employed", "student_working")


def current_shift(schedule: dict) -> str:
    """The shift a persona works now; rotating shifts are read from their current hours."""
    kind = schedule["schedule_type"]
    if kind != "rotating":
        return kind
    start = schedule["work_hours"][0]
    return "night" if start >= 21 or start < 5 else "evening" if start >= 13 else "day"


def facts_from_persona(persona: dict, today: date) -> dict:
    """Rebuild the facts the moment sections need from a finished persona.

    This lets context, state and intent be recomputed for any instant of an
    existing persona -- the same path the generator uses for the snapshot.
    """
    sp = persona["stable_profile"]
    work = persona["work_and_occupation"]
    life = persona["life_context"]
    schedule = work["schedule"]
    status = work["occupation"]["status"]
    enrolled_level = sp["education"]["enrolled_in"]
    return {
        "age": age_on(date.fromisoformat(sp["demographics"]["birth_date"]), today),
        "country": sp["residency"]["country"],
        "status": status,
        "occupation": work["occupation"]["occupation"],
        "working": status in WORKING_STATUSES,
        "enrolled": enrolled_level is not None,
        "enrolled_level": enrolled_level,
        "study_hours": schedule["study_hours"],
        "days_off": schedule["days_off"],
        "this_week_shift": current_shift(schedule),
        "exerciser": work["exercise"]["days_per_week"] > 0,
        "arrangement": life["living_situation"]["living_arrangement"],
        "partnered": life["family_and_relationships"]["romantic_relationship"]["status"] in ("dating", "cohabiting", "married"),
        "minors": [c for c in life["family_and_relationships"]["children"] if c["age"] < 18],
        "has_car": "car_audio" in persona["platform_and_devices"]["devices"],
    }
