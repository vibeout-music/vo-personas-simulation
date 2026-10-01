"""stable_profile: country, age, gender, languages, education, chronotype."""

from __future__ import annotations

import math
from datetime import date
from zoneinfo import ZoneInfo

from ..draft import Draft, age_on, life_stage_for
from ..sampling import clamp, r2, unit, weighted
from ..tables import COUNTRIES, EDUCATION_NEXT, SYLLABLES

# Age at which a level is usually started, used for enrolment.
EDUCATION_START_AGE = {"secondary": 11, "vocational": 16, "bachelor": 17, "master": 21, "doctorate": 23}


def sample_age(rng) -> int:
    # Music-app population: skewed towards teens and young adults, long tail to 85.
    return int(clamp(round(13 + rng.lognormvariate(math.log(13), 0.65)), 13, 85))


def sample_birth_date(rng, age: int, today: date) -> date:
    month = rng.randint(1, 12)
    day = rng.randint(1, 28 if month == 2 else 30 if month in (4, 6, 9, 11) else 31)
    year = today.year - age
    if (month, day) > (today.month, today.day):
        year -= 1  # birthday not reached yet this year
    return date(year, month, day)


def sample_education(rng, age: int) -> dict:
    if age < 16 or (age < 18 and rng.random() < 0.88):
        return {"highest_completed": "primary", "enrolled_in": "secondary"}
    if age < 18:
        return {"highest_completed": "secondary", "enrolled_in": "vocational"}

    older = 0.7 if age > 55 else 1.0
    options = {"secondary": 5, "vocational": 2 if age >= 19 else 0}
    options["bachelor"] = (4 if age >= 22 else 1.5 if age == 21 else 0) * older
    options["master"] = (1.5 if age >= 24 else 0.5 if age == 23 else 0) * older
    options["doctorate"] = 0.3 * older if age >= 28 else 0
    highest = weighted(rng, options)

    p_enrolled = 0.7 if age <= 22 else 0.3 if age <= 26 else 0.12 if age <= 35 else 0.04
    candidates = [lvl for lvl in EDUCATION_NEXT[highest] if age >= EDUCATION_START_AGE[lvl]]
    enrolled = rng.choice(candidates) if candidates and rng.random() < p_enrolled else None
    return {"highest_completed": highest, "enrolled_in": enrolled}


def build(d: Draft) -> None:
    rng = d.rng
    country = weighted(rng, {c: v["weight"] for c, v in COUNTRIES.items()})
    cdata = COUNTRIES[country]
    tz = rng.choice(cdata["tz"])
    d.local = d.when.astimezone(ZoneInfo(tz))

    age = sample_age(rng)
    birth = sample_birth_date(rng, age, d.local.date())
    assert age_on(birth, d.local.date()) == age

    sex = rng.choice(["male", "female"])
    roll = rng.random()
    if roll < 0.94:
        identity = "man" if sex == "male" else "woman"
    elif roll < 0.98:
        identity = "non_binary"
    else:
        identity = "trans_woman" if sex == "male" else "trans_man"

    urbanicity = unit(rng, cdata["urban"], 6)
    environment = "urban" if urbanicity >= 0.7 else "suburban" if urbanicity >= 0.35 else "rural"

    languages = [{"code": cdata["lang"], "proficiency": 1.0, "is_primary": True}]
    for code, p in cdata["second"].items():
        # Younger and more urban people are more likely to speak a second language.
        if rng.random() < p * (1.2 if age < 35 else 0.8) * (0.7 + 0.6 * urbanicity):
            languages.append({"code": code, "proficiency": unit(rng, 0.55, 4), "is_primary": False})

    education = sample_education(rng, age)
    birth_year = birth.year
    formative = [birth_year + 12, min(birth_year + 22, d.local.year)]

    d.persona["stable_profile"] = {
        "demographics": {
            "name_alias": "".join(rng.choice(SYLLABLES) for _ in range(rng.randint(2, 4))).capitalize(),
            "birth_date": birth.isoformat(),
            "age": age,
            "gender": sex,
            "gender_identity": identity,
            "life_stage": life_stage_for(age),
        },
        "residency": {"country": country, "timezone": tz, "environment": environment, "urbanicity": urbanicity},
        "languages": languages,
        "education": education,
        "economic_situation": None,       # set by the work section
        "socioeconomic_security": None,
        "cultural_exposure": r2(clamp(0.2 + 0.15 * (len(languages) - 1) + 0.3 * urbanicity + rng.gauss(0, 0.12))),
        # 0 = strong morning type, 1 = strong evening type. Adolescents skew late.
        "chronotype": unit(rng, 0.65 if age < 25 else 0.5 if age < 50 else 0.35, 5),
        "formative_music_years": formative,
    }
    d.facts.update(country=country, age=age, enrolled=education["enrolled_in"] is not None)
