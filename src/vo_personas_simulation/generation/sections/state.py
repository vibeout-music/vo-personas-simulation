"""mutable_state: the persona's latent state at the snapshot, derived from traits and context."""

from __future__ import annotations

import math
from datetime import date, datetime

from ..draft import Draft
from ..sampling import clamp, near, r2, unit

# Days for a life event's emotional weight to fall to ~37%. Grief and
# separation linger for months; most other events fade within weeks.
EVENT_FADE_DAYS = {"bereavement": 120, "divorce_process": 90, "breakup": 45, "job_loss": 60, "illness": 60,
                   "new_baby": 90, "financial_trouble": 60}
DEFAULT_FADE_DAYS = 30
LONELY_EVENTS = {"bereavement", "breakup", "divorce_process", "moving_house", "moved_out_of_parents_home"}


def life_event_pressure(p: dict, today: date) -> tuple[float, float, bool]:
    """(valence push, negative load, loneliness trigger) from active life events.

    Recent events weigh more, and people who recover quickly are less shaken:
    the same loss hits two people differently.
    """
    resilience = 1 - 0.5 * p["emotional_profile"]["dynamics"]["recovery_rate"]
    valence = negative = 0.0
    lonely = False
    for ev in p["life_context"]["life_events"]["active_life_events"]:
        days_ago = max(0, (today - date.fromisoformat(ev["started_on"])).days)
        fade = math.exp(-days_ago / EVENT_FADE_DAYS.get(ev["event_type"], DEFAULT_FADE_DAYS))
        push = ev["valence_impact"] * ev["intensity"] * fade * resilience
        valence += push
        negative += max(0.0, -push)
        lonely |= ev["event_type"] in LONELY_EVENTS and fade > 0.5
    return valence, negative, lonely


def build(d: Draft) -> None:
    rng, f = d.rng, d.facts
    p = d.persona
    ctx = p["current_context"]
    base = p["emotional_profile"]["baseline"]
    vol = p["emotional_profile"]["dynamics"]["volatility"]
    sleep_traits = p["neurobiology"]["sleep_characteristics"]
    activity = ctx["activity_and_location"]["activity"]
    event = ctx["event_of_the_day"]
    weather = ctx["environmental_conditions"]["weather"]
    reactions = p["environmental_sensitivities"]["weather_and_time"]["weather_mood_impact"]

    # --- sleep last night ---------------------------------------------------
    bad_night = event["event_type"] == "bad_night_sleep"
    infant = any(c["age"] < 2 for c in f["minors"])
    hours = clamp(sleep_traits["average_sleep_hours"] + rng.gauss(0, 0.7) - (1.8 if bad_night else 0) - (0.6 if infant else 0), 2, 12)
    if bad_night:
        hours = min(hours, sleep_traits["average_sleep_hours"] - 1)
    quality = r2(clamp(sleep_traits["sleep_quality"] + rng.gauss(0, 0.1) - (0.3 if bad_night else 0)))
    debt = round(max(0.0, sleep_traits["average_sleep_hours"] - hours), 1)

    # --- energy follows the body clock (night workers are shifted) ----------
    hour = datetime.fromisoformat(ctx["temporal"]["local_time"]).hour
    peak = 10 + 8 * p["stable_profile"]["chronotype"]
    if f["this_week_shift"] == "night" and not f["work_free"]:
        peak = (peak + 12) % 24
    circadian = math.cos(2 * math.pi * (hour - peak) / 24)
    energy = r2(clamp(0.5 + 0.3 * circadian - 0.08 * debt + 0.15 * (quality - 0.5) + rng.gauss(0, 0.08)))
    if activity == "sleeping":
        energy = min(energy, 0.25)

    event_val = event["valence_impact"] or 0.0
    event_aro = event["arousal_impact"] or 0.0
    life_val, life_neg, life_lonely = life_event_pressure(p, d.local.date())
    weather_val = (reactions["rainy_day_reaction"] if weather["condition"] in ("drizzle", "rain", "storm")
                   else reactions["sunny_day_reaction"] * weather["sunlight"] if weather["condition"] in ("clear", "partly_cloudy")
                   else reactions["overcast_reaction"])
    stress = r2(clamp(base["stress"] + (0.1 if activity in ("working", "commuting", "studying", "childcare") else -0.08)
                      + 0.3 * max(0.0, -event_val) + 0.6 * life_neg + 0.05 * debt + rng.gauss(0, 0.08)))
    noise = lambda: rng.gauss(0, 0.1 + 0.3 * vol)  # noqa: E731
    # tanh saturates softly: strong pushes approach the extremes without reaching them.
    valence = r2(math.tanh(base["valence"] + 0.6 * event_val + 1.2 * life_val + 0.25 * weather_val - 0.2 * (stress - base["stress"]) + noise()))
    arousal = r2(math.tanh(0.5 * base["arousal"] + 0.8 * (energy - 0.5) + 0.4 * event_aro + noise()))

    alone = ctx["social_context"]["social_company"] in ("alone", "strangers")
    loneliness = r2(clamp(p["life_context"]["social_connections"]["baseline_loneliness"] + (0.12 if alone else -0.12)
                          + (0.15 if life_lonely else 0) + rng.gauss(0, 0.06)))
    rumination = r2(clamp(p["psychology"]["cognitive_style"]["rumination_tendency"] * (0.4 + 0.6 * max(0.0, -valence) + life_neg)
                          + rng.gauss(0, 0.05)))

    pressure_events = {"exam_today", "work_deadline"}
    goal_pressure = 0.2 + 0.4 * (event["event_type"] in pressure_events) + 0.1 * any(
        ev["event_type"] in ("exam_period", "work_overload") for ev in p["life_context"]["life_events"]["active_life_events"])
    concerns = p["psychology"]["insecurities_and_fears"]["concerns"]
    insecurity = rng.choice(concerns) if rng.random() < p["psychology"]["big_five"]["neuroticism"] * 0.7 else None
    load = 1 - ctx["listening_control"]["available_attention"]

    p["mutable_state"] = {
        "timestamp": ctx["timestamp"],
        "current_affect": {
            "valence": valence,
            "arousal": arousal,
            "dominance": r2(math.tanh(base["dominance"] + 0.2 * event_val + noise())),
            "intensity": r2(clamp(0.2 + 0.5 * max(abs(valence), abs(arousal)) + 0.2 * vol + rng.gauss(0, 0.05))),
        },
        "physiological_state": {
            "stress": stress,
            "energy": energy,
            "fatigue": r2(clamp(1 - energy + 0.05 * debt + rng.gauss(0, 0.04))),
            "sleep": {"hours_last_night": round(hours, 1), "quality": quality, "sleep_debt": debt},
        },
        "cognitive_state": {
            "attention_capacity": r2(clamp(0.3 + 0.6 * energy - (0.15 if p["neurobiology"]["neurodivergence"]["has_adhd"] else 0) + rng.gauss(0, 0.05))),
            "cognitive_load": r2(clamp(load)),
            "rumination": rumination,
            "boredom": r2(clamp((0.5 if activity in ("commuting", "running_errands", "household_chores") else 0.2) - 0.3 * load + rng.gauss(0, 0.08))),
        },
        "social_emotional_state": {
            "loneliness": loneliness,
            "social_connectedness": near(rng, 1 - loneliness, 0.08),
        },
        "active_pressures": {"active_goal_pressure": r2(clamp(goal_pressure + rng.gauss(0, 0.08))), "active_insecurity": insecurity},
        "music_satiation": unit(rng, 0.3, 4),
        "per_track_fatigue": {},  # no listening history yet
    }
