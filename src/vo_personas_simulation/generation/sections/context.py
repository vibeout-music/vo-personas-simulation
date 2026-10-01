"""current_context: the moment of the snapshot, derived from the persona's schedule and home."""

from __future__ import annotations

import math
from datetime import datetime

from ..draft import Draft
from ..sampling import clamp, r2, unit, weighted
from ..tables import ACTIVITIES, COUNTRIES, DAILY_EVENTS, OCCUPATIONS

MINOR_FORBIDDEN_LOCATIONS = {"bar"}
PERSONAL_OUTPUTS = {"headphones", "earbuds"}


def in_window(hour: int, window) -> bool:
    start, end = window
    return start <= hour < end if start <= end else hour >= start or hour < end


def day_length(local: datetime, south: bool) -> float:
    doy = local.timetuple().tm_yday
    season = math.cos(2 * math.pi * (doy - 172) / 365) * (-1 if south else 1)  # +1 at local summer solstice
    return 12 + 2.5 * season


def daylight_factor(local: datetime, south: bool) -> float:
    """0 at night, up to 1 at solar noon."""
    length = day_length(local, south)
    sunrise, sunset = 12 - length / 2, 12 + length / 2
    h = local.hour + local.minute / 60
    if h <= sunrise or h >= sunset:
        return 0.0
    return math.sin(math.pi * (h - sunrise) / (sunset - sunrise))


def build_weather(rng, country: str, local: datetime) -> dict:
    c = COUNTRIES[country]
    mean, amp = c["temp"]
    doy = local.timetuple().tm_yday
    peak = 20 if c["south"] else 200
    diurnal = 4 * math.sin(2 * math.pi * (local.hour - 9) / 24)
    temp = mean + amp * math.cos(2 * math.pi * (doy - peak) / 365) + diurnal + rng.gauss(0, 3)
    wet = c["wet"]
    condition = weighted(rng, {"clear": 3, "partly_cloudy": 3, "cloudy": 2, "fog": 0.4, "drizzle": wet * 3, "rain": wet * 4, "storm": wet * 1})
    if condition in ("rain", "drizzle") and temp < 1:
        condition = "snow"
    cloud = {"clear": 0.05, "partly_cloudy": 0.35, "cloudy": 0.8, "fog": 0.9, "drizzle": 0.85, "rain": 0.9, "storm": 0.97, "snow": 0.9}[condition]
    precipitation = {"drizzle": unit(rng, 0.2, 8), "rain": unit(rng, 0.55, 6), "storm": unit(rng, 0.85, 8), "snow": unit(rng, 0.5, 5)}.get(condition, 0.0)
    return {
        "condition": condition,
        "temperature_c": round(temp),
        "sunlight": r2(daylight_factor(local, c["south"]) * (1 - 0.8 * cloud)),
        "precipitation": precipitation,
        "daylight_hours": round(day_length(local, c["south"]), 1),
    }


def time_of_day(hour: int) -> str:
    return "night" if hour < 6 else "morning" if hour < 12 else "afternoon" if hour < 18 else "evening" if hour < 22 else "late_night"


def pick_activity(d: Draft, hour: int, work_free: bool, study_free: bool) -> tuple[str, str]:
    """Returns (activity, reason) where reason is work/study/commute/free."""
    rng, f = d.rng, d.facts
    p = d.persona
    work = p["work_and_occupation"]
    late = p["stable_profile"]["chronotype"]
    work_hours = work["schedule"]["work_hours"] if f["working"] else None
    study_hours = f["study_hours"]
    commute = work["commute"]

    work_hours = None if work_free else work_hours
    study_hours = None if study_free else study_hours
    if work_hours and in_window(hour, work_hours):
        return ("working" if rng.random() < 0.92 else "eating"), "work"
    if study_hours and in_window(hour, study_hours):
        return ("studying" if rng.random() < 0.9 else "eating"), "study"
    if commute["mode"] != "none":
        span = max(1, math.ceil(commute["minutes_each_way"] / 60))
        for start, end in (h for h in (work_hours, study_hours) if h):
            if in_window(hour, ((start - span) % 24, start)) or in_window(hour, (end, (end + span) % 24)):
                if rng.random() < 0.75:
                    return "commuting", "commute"
    free_day = work_free and study_free

    night_worker = f["working"] and f["this_week_shift"] == "night" and not work_free
    sleep_window = (8, 15) if night_worker else (round(23 + 1.5 * late) % 24, round(6 + 2.5 * late))
    w = {a: 0.0 for a in ACTIVITIES}
    if in_window(hour, sleep_window):
        w.update(sleeping=10, winding_down=1 + late, relaxing=0.5, gaming=0.5 * late if f["age"] < 40 else 0)
    elif hour < 10:
        w.update(waking_up=4, eating=1.5, household_chores=0.5)
    elif hour < 18:
        w.update(relaxing=3, household_chores=2, running_errands=2, socializing=1.5, cooking=1,
                 eating=2 if 12 <= hour <= 14 else 0.4)
    elif hour < 21:
        w.update(cooking=2.5, relaxing=2, running_errands=1, socializing=1.5, household_chores=1, eating=1.5)
    else:
        w.update(relaxing=4, gaming=1.5 if f["age"] < 40 else 0.3, socializing=2 if free_day else 0.8, winding_down=2)

    slot = work["exercise"]["time_slot"]
    if slot and not in_window(hour, sleep_window):
        slot_hours = {"early_morning": (6, 8), "lunch": (12, 14), "afternoon": (15, 18), "evening": (18, 21)}[slot]
        if in_window(hour, slot_hours):
            w["exercising"] = 10 * work["exercise"]["days_per_week"] / 7
    if f["enrolled"] and hour >= 16 and not in_window(hour, sleep_window):
        w["studying"] = 1.5
    if p["life_context"]["living_situation"]["caregiving_load"] > 0.3 and (7 <= hour < 9 or 17 <= hour < 21):
        w["childcare"] = 3 * p["life_context"]["living_situation"]["caregiving_load"]
    if f["status"] == "homemaker" and 9 <= hour < 18:
        w["household_chores"] += 3
    return weighted(rng, w), "free"


def pick_daily_event(rng, f: dict, work: dict, exclude=()):
    def ok(req):
        return {
            None: True, "partner": f["partnered"], "employed": f["working"], "enrolled": f["enrolled"],
            "family": f["arrangement"] in ("with_parents", "with_family", "with_partner_and_children", "single_parent"),
            "car": work["commute"]["mode"] == "car", "transit": work["commute"]["mode"] in ("public_transport", "school_bus"),
            "young_child": any(c["age"] < 12 for c in f["minors"]), "adult": f["age"] >= 18, "exerciser": f["exerciser"],
        }[req]
    options = [k for k, v in DAILY_EVENTS.items() if ok(v[3]) and k not in exclude]
    return rng.choice(options)


def build(d: Draft) -> None:
    rng, f = d.rng, d.facts
    p = d.persona
    sp = p["stable_profile"]
    work = p["work_and_occupation"]
    lc = p["life_context"]
    devices = p["platform_and_devices"]["devices"]
    local = d.local
    hour = local.hour

    birth = sp["demographics"]["birth_date"]
    mmdd = local.strftime("%m-%d")
    holiday = mmdd in COUNTRIES[f["country"]]["holidays"]
    special = "birthday" if birth[5:] == mmdd else "public_holiday" if holiday else None
    weekend = local.weekday() >= 5
    work_free = holiday or local.weekday() in f["days_off"]
    study_free = holiday or weekend
    day_type = "holiday" if holiday else "weekend" if weekend else "weekday"

    activity, reason = pick_activity(d, hour, work_free, study_free)
    spec = ACTIVITIES[activity]
    commute_mode = work["commute"]["mode"]

    if activity == "commuting":
        location = {"car": "car", "public_transport": "public_transport", "school_bus": "public_transport",
                    "walking": "street", "cycling": "street"}[commute_mode]
        audio = {"car": "car_audio", "cycling": "none"}.get(commute_mode, rng.choice(["earbuds", "headphones"]))
        device = rng.choice([x for x in spec["dev"] if x in devices] or ["phone"])
    elif activity == "working":
        env = work["occupation"]["work_environment"]
        location = OCCUPATIONS[f["occupation"]]["loc"] if f["occupation"] in OCCUPATIONS else "home"
        if env in ("remote_home", "home"):
            location = "home"
        elif env == "hybrid":
            location = rng.choice(["home", "office"])
        can_listen = rng.random() < (work["schedule"]["can_listen_while_working"] or 0)
        if location == "car":
            audio, device = "car_audio", "phone"
        elif not can_listen:
            audio, device = "none", "phone"
        elif location == "home":
            audio = rng.choice(["headphones", "home_speakers", "earbuds"])
            device = rng.choice([x for x in ("laptop", "desktop", "phone") if x in devices])
        else:
            audio, device = rng.choice(["earbuds", "headphones"]), rng.choice([x for x in ("phone", "laptop") if x in devices])
    else:
        locations = [x for x in spec["loc"] if not (f["age"] < 18 and x in MINOR_FORBIDDEN_LOCATIONS)]
        location = "school" if reason == "study" else rng.choice(locations)
        device = rng.choice([x for x in spec["dev"] if x in devices] or ["phone"])
        audio = rng.choice(spec["out"])
        if audio == "smart_speaker" and "smart_speaker" not in devices:
            audio = "phone_speaker"
        if location == "home" and audio in ("home_speakers", "smart_speaker") and lc["living_situation"]["privacy"] < 0.3:
            audio = "headphones"
        if location not in ("home", "friend_home"):
            # Stationary equipment only exists at home (or a friend's home).
            if audio in ("home_speakers", "smart_speaker", "phone_speaker"):
                audio = "venue_speakers" if location in ("bar", "restaurant", "store", "gym") else rng.choice(["earbuds", "headphones"])
            if device in ("tv", "console", "desktop", "smart_speaker"):
                device = "phone"
        if reason == "study":
            audio = rng.choice(["earbuds", "none", "none"])
            device = "phone" if audio == "none" else device

    arrangement = f["arrangement"]
    if activity == "socializing":
        company = rng.choice(["friends", "friends", "family"] + (["partner"] if f["partnered"] else []))
    elif activity == "childcare":
        company = "family"
    elif activity in ("working", "studying") and location != "home":
        company = "coworkers" if activity == "working" else "classmates"
    elif activity == "commuting":
        company = "strangers" if location == "public_transport" else "alone"
    elif location == "home":
        household = {"alone": ["alone"], "shared": ["alone", "housemates"], "with_parents": ["alone", "family"],
                     "with_family": ["alone", "family"], "with_partner": ["alone", "partner"],
                     "with_partner_and_children": ["alone", "partner", "family"], "single_parent": ["alone", "family"]}[arrangement]
        company = rng.choice(household)
    elif location in ("gym", "store", "street", "restaurant", "library", "outdoors", "bar"):
        company = rng.choice(["alone", "alone", "friends", "strangers"])
    else:
        company = "alone"

    # --- how much control and room for music there is ---------------------
    personal = audio in PERSONAL_OUTPUTS or (audio == "car_audio" and company == "alone")
    control = 0.9 if personal else 0.2 if audio == "venue_speakers" else 0.6 if company == "alone" else 0.45
    load = {"working": work["work_characteristics"]["cognitive_load"], "studying": 0.75, "sleeping": 0.95,
            "commuting": 0.55 if commute_mode == "car" else 0.2, "socializing": 0.6, "childcare": 0.7,
            "exercising": 0.3, "gaming": 0.6}.get(activity, 0.3)
    minutes = {
        "commuting": work["commute"]["minutes_each_way"], "exercising": rng.randint(30, 90), "sleeping": 0,
        "working": rng.randint(30, 240), "studying": rng.randint(30, 180), "relaxing": rng.randint(20, 150),
        "winding_down": rng.randint(15, 60), "socializing": rng.randint(30, 180), "gaming": rng.randint(30, 150),
    }.get(activity, rng.randint(10, 60))
    privacy = lc["living_situation"]["privacy"] if location == "home" else 0.9 if location == "car" and company == "alone" else 0.2

    event = pick_daily_event(rng, f, work) if rng.random() < 0.45 else None
    recent = []
    for _ in range(rng.randint(0, 2)):
        ev = pick_daily_event(rng, f, work, exclude=[event, *[r["event_type"] for r in recent]])
        recent.append({"event_type": ev, "days_ago": rng.randint(1, 6)})

    p["current_context"] = {
        "timestamp": d.when.isoformat().replace("+00:00", "Z"),
        "temporal": {"local_time": local.isoformat(timespec="minutes"), "day_type": day_type, "time_of_day": time_of_day(hour)},
        "activity_and_location": {"activity": activity, "location_type": location},
        "social_context": {"social_company": company},
        "listening_control": {
            "control_over_music": r2(clamp(control + rng.gauss(0, 0.05))),
            "available_attention": r2(clamp(1 - load + rng.gauss(0, 0.05))),
            "available_minutes": minutes,
            "privacy": r2(clamp(privacy)),
        },
        "technical_setup": {"device": device, "audio_output": audio},
        "environmental_conditions": {"weather": build_weather(rng, f["country"], local)},
        "recent_events": recent,
        "event_of_the_day": {
            "event_type": event,
            "description": DAILY_EVENTS[event][2] if event else None,
            "valence_impact": DAILY_EVENTS[event][0] if event else None,
            "arousal_impact": DAILY_EVENTS[event][1] if event else None,
        },
        "special_dates": {"holiday_or_special": special},
        "song_of_the_moment": None,  # needs the music catalogue
    }
    f["work_free"] = work_free
