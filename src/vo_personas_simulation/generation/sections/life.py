"""life_context and neurobiology: relationships, household, social life, health, money, life events, sleep."""

from __future__ import annotations

import math
from datetime import date, timedelta

from ..draft import Draft, age_on
from ..sampling import clamp, near, poisson, r2, unit, weighted
from ..tables import LIFE_EVENTS

PARTNERED = ("dating", "cohabiting", "married")


def sample_relationship(rng, age: int) -> str:
    if age < 18:
        return weighted(rng, {"single": 8, "dating": 2})
    if age < 25:
        return weighted(rng, {"single": 6, "dating": 3, "cohabiting": 1, "married": 0.3})
    if age < 65:
        return weighted(rng, {"single": 3, "dating": 1.5, "cohabiting": 2, "married": 4, "divorced": 1 if age >= 22 else 0})
    return weighted(rng, {"single": 1, "married": 5, "divorced": 1.5, "widowed": 2.5})


def sample_children(rng, age: int, status: str) -> list[dict]:
    if age < 18:
        return []
    had_partner = status in ("cohabiting", "married", "divorced", "widowed")
    lam = clamp((age - 20) / 15, 0, 1) * (1.8 if had_partner else 0.3)
    oldest_possible = min(age - 16, 50)
    ages = []
    for _ in range(min(poisson(rng, lam), 5)):
        if ages and rng.random() < 0.03:
            ages.append(ages[-1])  # twins
            continue
        free = [a for a in range(oldest_possible + 1) if a not in ages]
        ages.append(rng.choice(free))
    return [{"age": a} for a in sorted(ages, reverse=True)]


def sample_arrangement(rng, age: int, relationship: str, children: list, status: str) -> str:
    minors = any(c["age"] < 18 for c in children)
    if age < 18:
        return "with_parents"
    if relationship in ("cohabiting", "married"):
        return "with_partner_and_children" if minors else "with_partner"
    if minors and (relationship != "divorced" or rng.random() < 0.6):
        return "single_parent"
    if age < 25:
        return weighted(rng, {"with_parents": 5 + 2 * (status == "student"), "shared": 3, "alone": 1.5})
    if age >= 65:
        return weighted(rng, {"alone": 5, "with_family": 2})
    return weighted(rng, {"alone": 5, "shared": 2 if age < 40 else 0.4, "with_parents": 1.5 if age < 35 else 0.2})


def event_allowed(event: str, f: dict, lc: dict) -> bool:
    spec = LIFE_EVENTS[event]
    lo, hi = spec["ages"]
    if not lo <= f["age"] <= hi:
        return False
    rel = lc["family_and_relationships"]["romantic_relationship"]["status"]
    req = spec["requires"]
    return {
        None: True,
        "enrolled": f["enrolled"],
        "dating": rel == "dating",
        "single": rel == "single",
        "engaged_possible": rel in ("dating", "cohabiting") and f["age"] >= 20,
        "divorced": rel == "divorced",
        "baby": any(c["age"] == 0 for c in lc["family_and_relationships"]["children"]),
        "employed": f["status"] in ("employed", "self_employed", "student_working"),
        "unemployed": f["status"] == "unemployed",
        "retired": f["status"] == "retired",
        "not_with_parents": lc["living_situation"]["living_arrangement"] != "with_parents",
        "financial_pressure": lc["financial"]["financial_pressure"] > 0.55,
    }[req]


def build(d: Draft) -> None:
    rng, f = d.rng, d.facts
    age, status = f["age"], f["status"]
    psy = d.persona["psychology"]["big_five"]
    e, a, n, c = psy["extraversion"], psy["agreeableness"], psy["neuroticism"], psy["conscientiousness"]
    sp = d.persona["stable_profile"]

    relationship = sample_relationship(rng, age)
    children = sample_children(rng, age, relationship)
    arrangement = sample_arrangement(rng, age, relationship, children, status)
    minors = [ch for ch in children if ch["age"] < 18]
    household_size = 1 + {"alone": 0, "shared": 2, "with_parents": 2, "with_partner": 1, "with_family": 2,
                          "with_partner_and_children": 1, "single_parent": 0}[arrangement] + (len(minors) if arrangement in ("with_partner_and_children", "single_parent") else 0)

    partnered = relationship in PARTNERED
    caregiving = sum(1.0 if ch["age"] < 6 else 0.6 if ch["age"] < 12 else 0.25 for ch in minors
                     ) if arrangement in ("with_partner_and_children", "single_parent") else 0
    if arrangement == "single_parent":
        caregiving *= 1.5
    if 45 <= age <= 70 and rng.random() < 0.06:
        caregiving += 0.8  # caring for an elderly parent

    privacy_mean = {"alone": 0.9, "with_partner": 0.65, "shared": 0.4, "with_parents": 0.35, "with_family": 0.45,
                    "with_partner_and_children": 0.3, "single_parent": 0.4}[arrangement]
    social_support = unit(rng, 0.3 + 0.25 * e + 0.2 * a + (0.1 if partnered else 0), 5)
    loneliness = r2(clamp(0.15 + 0.35 * n + 0.25 * (arrangement == "alone") - 0.3 * social_support + 0.1 * (not partnered) + rng.gauss(0, 0.1)))
    network = max(2, round(rng.lognormvariate(math.log(6 + 25 * e), 0.5)))
    economic = sp["economic_situation"]
    financial_pressure = r2(clamp(0.9 - 0.8 * economic + 0.07 * len(minors) + (0.15 if status == "unemployed" else 0) + rng.gauss(0, 0.08)))
    exercise_days = d.get("work_and_occupation.exercise.days_per_week")

    lc = {
        "family_and_relationships": {
            "children": children,
            "family": {
                "closeness": unit(rng, 0.55 + 0.1 * a, 4),
                "support": unit(rng, 0.55, 4),
                "baseline_tension": unit(rng, 0.25 + 0.3 * n, 4),
                "music_influence": unit(rng, 0.5 if arrangement == "with_parents" else 0.3 if age < 30 else 0.15, 5),
            },
            "romantic_relationship": {
                "status": relationship,
                "satisfaction": unit(rng, 0.7 - 0.2 * n, 5) if partnered else None,
                "emotional_salience": unit(rng, 0.6 if partnered else 0.75 if relationship in ("divorced", "widowed") else 0.3, 5),
            },
        },
        "living_situation": {
            "living_arrangement": arrangement,
            "privacy": unit(rng, privacy_mean, 8),
            "background_noise": r2(clamp(0.1 + 0.3 * sp["residency"]["urbanicity"] + 0.08 * household_size + rng.gauss(0, 0.08))),
            "caregiving_load": r2(clamp(caregiving / 2.5)),
        },
        "social_connections": {
            "social_support": social_support,
            "social_battery_capacity": near(rng, 0.2 + 0.7 * e, 0.1),
            "network_size": network,
            "contact_frequency": max(0, round(network * (0.2 + 0.5 * e) * rng.uniform(0.6, 1.4))),  # contacts per week
            "sense_of_belonging": near(rng, 1 - loneliness, 0.1),
            "baseline_loneliness": loneliness,
            "peer_music_influence": unit(rng, 0.15 + (0.3 if age < 25 else 0.1 if age < 50 else 0.0) + 0.35 * d.get("psychology.personality_traits.social_conformity"), 8),
        },
        "health": {
            "physical_health": r2(clamp(0.8 - 0.006 * max(0, age - 30) + 0.03 * exercise_days + rng.gauss(0, 0.1))),
        },
        "life_events": {"active_life_events": []},
        "financial": {"financial_pressure": financial_pressure},
    }

    # Life events that fit the person's situation; a new baby always shows up.
    events = []
    candidates = [ev for ev in LIFE_EVENTS if event_allowed(ev, f, lc)]
    if "new_baby" in candidates and rng.random() < 0.8:
        events.append("new_baby")
    for _ in range(min(poisson(rng, 0.8), 2)):
        options = [ev for ev in candidates if ev not in events]
        if options:
            events.append(rng.choice(options))
    today = d.local.date()
    birth = date.fromisoformat(d.persona["stable_profile"]["demographics"]["birth_date"])
    last_birthday = date(today.year if (today.month, today.day) >= (birth.month, birth.day) else today.year - 1, birth.month, birth.day)
    active = []
    for ev in events:
        # Absolute date, so the event keeps ageing as later moments are simulated.
        started = today - timedelta(days=rng.randint(0, 120))
        if not event_allowed(ev, {**f, "age": age_on(birth, started)}, lc):
            started = today - timedelta(days=rng.randint(0, (today - last_birthday).days))  # it began at their current age
        active.append({
            "event_type": ev,
            "started_on": started.isoformat(),
            "valence_impact": r2(LIFE_EVENTS[ev]["valence"] * rng.uniform(0.6, 1.2)),
            "intensity": unit(rng, 0.4 + 0.3 * abs(LIFE_EVENTS[ev]["valence"]), 5),
        })
    lc["life_events"]["active_life_events"] = active
    d.persona["life_context"] = lc

    # --- neurobiology (sleep depends on age, infants, shifts) --------------
    infant = any(ch["age"] < 2 for ch in minors) and arrangement != "alone"
    night = f["this_week_shift"] == "night"
    avg_sleep = clamp(rng.gauss(8.6 if age < 18 else 7.3 if age < 65 else 7.0, 0.7) - (0.8 if infant else 0) - (0.5 if night else 0), 4.5, 10.5)
    d.persona["neurobiology"] = {
        "neurodivergence": {"has_adhd": rng.random() < (0.08 if age < 30 else 0.04), "sensory_sensitivity": unit(rng, 0.4 + 0.2 * n, 3)},
        "sleep_characteristics": {
            "average_sleep_hours": round(avg_sleep, 1),
            "sleep_quality": unit(rng, 0.7 - 0.3 * n - (0.15 if infant else 0) - (0.1 if night else 0) + 0.05 * c, 5),
        },
    }
    f.update(has_children=bool(children), partnered=partnered, minors=minors, arrangement=arrangement,
             household_size=household_size, relationship=relationship)
