"""routine_and_behavior: daily routine, listening windows and app behaviour."""

from __future__ import annotations

import math

from ..draft import Draft
from ..sampling import clamp, near, r2, unit, weighted
from .emotional import bias


def routine_archetype(f: dict, schedule_type: str, caregiving: float) -> str:
    status = f["status"]
    if status == "student":
        return "student"
    if status == "student_working":
        return "student_worker"
    if status == "retired":
        return "retiree"
    if status in ("unemployed", "homemaker"):
        return "caregiver" if caregiving > 0.4 else "homebound"
    if schedule_type in ("night", "rotating", "evening"):
        return "shift_worker"
    if schedule_type == "flexible" or status == "self_employed":
        return "flexible"
    return "nine_to_five"


def listening_windows(d: Draft, can_listen: float | None) -> list[dict]:
    """Recurring moments of the day that suit listening, derived from the schedule."""
    w = d.persona["work_and_occupation"]
    chrono = d.persona["stable_profile"]["chronotype"]
    windows = []
    hours = w["schedule"]["work_hours"]
    commute = w["commute"]
    if hours and commute["mode"] != "none":
        start, end = hours
        span = max(1, math.ceil(commute["minutes_each_way"] / 60))
        windows.append({"start_hour": (start - span) % 24, "end_hour": start, "typical_activity": "commuting"})
        windows.append({"start_hour": end, "end_hour": (end + span) % 24, "typical_activity": "commuting"})
    if hours and can_listen is not None and can_listen >= 0.5:
        windows.append({"start_hour": hours[0], "end_hour": hours[1], "typical_activity": "working"})
    slot = w["exercise"]["time_slot"]
    if slot:
        start = {"early_morning": 6, "lunch": 13, "afternoon": 16, "evening": 19}[slot]
        windows.append({"start_hour": start, "end_hour": start + 1, "typical_activity": "exercising"})
    evening = 20 + round(2 * chrono)
    windows.append({"start_hour": evening, "end_hour": (evening + 2) % 24, "typical_activity": "relaxing"})
    return sorted(windows, key=lambda x: x["start_hour"])


def build(d: Draft) -> None:
    rng, f = d.rng, d.facts
    b = lambda k: bias(d, k)  # noqa: E731
    p = d.persona
    psy = p["psychology"]
    c, e = psy["big_five"]["conscientiousness"], psy["big_five"]["extraversion"]
    impulsivity = psy["personality_traits"]["impulsivity"]
    work = p["work_and_occupation"]
    music = p["music_identity"]
    caregiving = p["life_context"]["living_situation"]["caregiving_load"]
    schedule_type = work["schedule"]["schedule_type"]
    archetype = routine_archetype(f, schedule_type, caregiving)

    sleep = p["neurobiology"]["sleep_characteristics"]["average_sleep_hours"]
    busy = (work["schedule"]["weekly_hours"] + 2 * work["commute"]["minutes_each_way"] / 60 * 5) / 7
    free_time = r2(clamp(24 - sleep - busy - 4 * caregiving - 2.5 + rng.gauss(0, 0.5), 0.5, 12))

    windows = listening_windows(d, work["schedule"]["can_listen_while_working"])
    lo = max(1, len(windows) - 1 + round(rng.gauss(0, 0.7)))
    hi = lo + max(0, round(rng.expovariate(1.0)))

    skip_rate = unit(rng, 0.35 + b("skip_rate") + 0.2 * (impulsivity - 0.5), 4)
    like_rate = unit(rng, 0.2 + b("like_rate"), 4)
    novelty = music["sensory_and_discovery"]["discovery"]["novelty_preference"]
    loyalty = music["sensory_and_discovery"]["discovery"]["artist_loyalty"]
    obsessive = unit(rng, 0.35 + b("obsessive_replay") + 0.2 * (1 - novelty), 3)
    active = unit(rng, 0.5 + b("active") + 0.2 * (music["importance_and_sophistication"]["identity_centrality"] - 0.5), 4)

    p["routine_and_behavior"] = {
        "daily_routine": {
            "daily_routine_archetype": archetype,
            "routine_strength": unit(rng, 0.3 + 0.4 * c + b("routine") - (0.15 if archetype == "shift_worker" else 0), 5),
            "daily_free_time_h": free_time,
        },
        "listening_windows": {"habitual_listening_windows": windows},
        "session_behavior": {
            "sessions_per_day": [lo, hi],
            "session_length_min": {"mean": max(5, round(rng.lognormvariate(math.log(28), 0.45))), "std": rng.randint(3, 20)},
        },
        "listening_initiation": {
            "session_start_mode": weighted(rng, {"intentional": 0.5 + active, "habitual": 0.5 + c, "ambient": 0.3 + music["listening_functions"]["background"]}),
            "active_selection_probability": active,
            "background_listening_probability": near(rng, music["listening_functions"]["background"], 0.1),
            "autoplay_acceptance": near(rng, 0.3 + 0.5 * music["sensory_and_discovery"]["discovery"]["recommendation_trust"] - 0.2 * (active - 0.5), 0.1),
        },
        "skip_behavior": {
            "skip_rate": skip_rate,
            "skip_patience_seconds": max(3, round((5 + 55 * (1 - skip_rate)) * rng.uniform(0.7, 1.3))),
            "tolerance_consecutive_bad_songs": max(1, round(1 + 5 * (1 - skip_rate) + rng.gauss(0, 0.7))),
        },
        "feedback_behavior": {
            "like_rate": like_rate,
            "explicit_feedback_propensity": near(rng, like_rate + 0.15, 0.08),
            "save_propensity": near(rng, 0.2 + 0.4 * active + 0.2 * like_rate, 0.1),
            "sharing_propensity": unit(rng, 0.2 + 0.25 * e + b("sharing"), 4),
        },
        "replay_and_habituation": {
            "repeat_propensity": near(rng, 0.25 + 0.3 * loyalty + 0.3 * obsessive, 0.1),
            "obsessive_replay": obsessive,
            "habituation": unit(rng, 0.3 + 0.35 * novelty + b("habituation"), 4),
            "completion_bias": near(rng, 0.8 - 0.6 * skip_rate, 0.1),
        },
        "baseline_listening": {
            "baseline_daily_listening_probability": unit(rng, 0.55 + 0.25 * music["importance_and_sophistication"]["identity_centrality"] + b("daily_listening"), 6),
        },
    }
