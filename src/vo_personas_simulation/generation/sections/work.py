"""work_and_occupation, economics and car ownership."""

from __future__ import annotations

from ..draft import Draft
from ..sampling import clamp, near, r2, unit, weighted
from ..tables import (COUNTRIES, EDUCATION_MIN_COMPLETION_AGE, EDUCATION_RANK, EXERCISE_TYPES, NON_WORKING,
                      OCCUPATIONS, SENIORITY, SHIFT_HOURS)

SELF_EMPLOYED = {"freelance_creative", "musician", "small_business_owner", "electrician", "tutor", "driver", "delivery_rider", "designer"}


def sample_status(rng, age: int, enrolled_level: str | None) -> str:
    if enrolled_level:
        if age < 16:
            return "student"
        if enrolled_level == "doctorate":
            return "student_working"  # doctoral candidates are paid researchers
        return "student_working" if rng.random() < (0.15 if age < 18 else 0.35) else "student"
    if age >= 67 and rng.random() < 0.9 or 60 <= age < 67 and rng.random() < 0.5:
        return "retired"
    return weighted(rng, {"employed": 75, "self_employed": 10, "unemployed": 7, "homemaker": 5})


def sample_occupation(rng, status: str, age: int, education: dict) -> str | None:
    """None when no occupation fits the person's age and education."""
    if status in NON_WORKING:
        return status
    if education["enrolled_in"] == "doctorate":
        return "researcher"
    rank = EDUCATION_RANK[education["highest_completed"]]
    eligible = {}
    for name, o in OCCUPATIONS.items():
        if not (o["ages"][0] <= age <= o["ages"][1] and o["edu"] <= rank):
            continue
        if status == "student_working" and not o.get("part_time"):
            continue
        if status == "self_employed" and name not in SELF_EMPLOYED:
            continue
        # People mostly work in jobs that match their education.
        gap = rank - o["edu"]
        eligible[name] = o["share"] * (2.0 if gap <= 1 and rank >= 2 else 1.0) * (0.25 if gap >= 3 else 1.0)
    return weighted(rng, eligible) if eligible else None


def job_title(occupation: str, status: str, years: int) -> str | None:
    if status in NON_WORKING:
        return None
    base = occupation.replace("_", " ").title()
    if status == "student_working":
        return f"Doctoral Researcher" if occupation == "researcher" else f"Part-time {base}"
    prefix = next(p for lo, hi, p in SENIORITY if lo <= years <= hi)
    return f"{prefix} {base}" if prefix else base


def build(d: Draft) -> None:
    rng, f = d.rng, d.facts
    sp = d.persona["stable_profile"]
    age, education = f["age"], sp["education"]
    c = d.get("psychology.big_five.conscientiousness")

    status = sample_status(rng, age, education["enrolled_in"])
    occupation = sample_occupation(rng, status, age, education)
    if occupation is None:  # e.g. an 85-year-old: no job fits any more
        status = occupation = "retired" if age >= 55 else "unemployed"
    working = status in ("employed", "self_employed", "student_working")
    years_experience = max(0, age - max(EDUCATION_MIN_COMPLETION_AGE[education["highest_completed"]], 18))
    o = OCCUPATIONS.get(occupation)

    # --- schedule -------------------------------------------------------
    study_hours = rng.choice(SHIFT_HOURS["school_hours"]) if education["enrolled_in"] else None
    part_time = False
    if o:
        shifts = [s for s in o["shifts"] if not (status == "student_working" and s in ("day", "school_hours"))] or ["evening"]
        schedule_type = weighted(rng, {s: 3 if s in ("day", "school_hours") else 1 for s in shifts})
        if schedule_type == "rotating":
            this_week = rng.choice(["day", "evening", "night"])
        else:
            this_week = schedule_type
        start, end = rng.choice(SHIFT_HOURS[this_week])
        part_time = status == "student_working" and occupation != "researcher" or (status == "employed" and rng.random() < 0.15)
        if part_time:
            end = start + rng.randint(4, 6)
        weekly = (rng.randint(10, 20) if status == "student_working" and part_time
                  else rng.randint(15, 30) if part_time
                  else rng.randint(20, 55) if status == "self_employed"
                  else rng.randint(35, 45))
        work_hours = [start, end % 24]
        works_weekends = schedule_type in ("rotating", "evening") or occupation in ("retail_worker", "hospitality_worker", "chef", "delivery_rider")
    elif status == "student":
        schedule_type, work_hours, weekly, works_weekends = "school_hours", list(study_hours), rng.randint(20, 32), False
    else:
        schedule_type, work_hours, weekly, works_weekends = "none", None, 0, False

    days_off = sorted(rng.sample(range(7), 2)) if works_weekends else [5, 6]

    # --- work characteristics --------------------------------------------
    if o:
        music_allowed = o["music"] if rng.random() < 0.85 else not o["music"]
        listen = unit(rng, o["listen"] if music_allowed else 0.08, 6)
        load, stress_mean = o["load"], o["stress"]
        env = rng.choice(o["env"])
    elif status == "student":
        music_allowed, listen = False, unit(rng, 0.3, 5)
        load, stress_mean, env = 0.6, 0.5, "school"
    else:
        music_allowed, listen = None, None
        load, stress_mean, env = 0.3, 0.3, NON_WORKING[occupation]["env"]
    autonomy = unit(rng, 0.8 if status == "self_employed" else 0.25 + 0.02 * min(years_experience, 20) if working else 0.6, 5)
    n = d.get("psychology.big_five.neuroticism")

    # --- economics --------------------------------------------------------
    income = o["income"] if o else NON_WORKING[occupation]["income"]
    if status in ("student", "student_working") and age < 25:
        income = 0.45  # reflects the family household
    income += 0.05 * EDUCATION_RANK[education["highest_completed"]] + 0.005 * min(years_experience, 20) - (0.12 if part_time and status == "employed" else 0)
    economic = unit(rng, income, 10)
    sp["economic_situation"] = economic
    sp["socioeconomic_security"] = near(rng, economic, 0.07)

    # --- commute and car --------------------------------------------------
    environment = sp["residency"]["environment"]
    no_commute = env in ("remote_home", "home", "vehicle", "street", "home_visits") and not education["enrolled_in"]
    rich_country = COUNTRIES[f["country"]]["premium"] > 0.4
    car_p = 0 if age < 18 else clamp((0.25 + 0.6 * economic) * {"urban": 0.6, "suburban": 1.1, "rural": 1.4}[environment] * (1.2 if rich_country else 0.7))
    has_car = rng.random() < car_p
    if no_commute:
        mode, minutes = "none", 0
    else:
        options = {
            "car": 6 if has_car else 0,
            "public_transport": {"urban": 5, "suburban": 2, "rural": 0.5}[environment],
            "walking": 2 if environment == "urban" else 0.7,
            "cycling": 1,
            "school_bus": 3 if age < 18 else 0,
        }
        mode = weighted(rng, options)
        minutes = max(5, min(120, round(rng.lognormvariate(3.2, 0.5) * (0.6 if mode == "walking" else 1))))

    # --- exercise ---------------------------------------------------------
    # Mean days per week: conscientious people train more, older people less.
    days = min(7, int(rng.expovariate(1 / ((0.8 + 3 * c) * (0.55 if age >= 65 else 1.0)))))
    if days == 0:
        slot, types = None, None
    else:
        slots = {"early_morning": 1.5 - sp["chronotype"], "evening": 0.5 + sp["chronotype"], "afternoon": 0.8}
        if work_hours and work_hours[0] < 8 and schedule_type != "night":
            slots["early_morning"] = 0
        if work_hours and schedule_type in ("evening",):
            slots["evening"] = 0
        if schedule_type in ("day", "school_hours") and status != "retired":
            slots["afternoon"] = 0.3
            slots["lunch"] = 0.6
        slot = weighted(rng, slots)
        allowed = [t for t in EXERCISE_TYPES if not (age >= 60 and t in ("team_sports", "martial_arts"))]
        types = rng.sample(allowed, rng.randint(1, 2))

    d.persona["work_and_occupation"] = {
        "occupation": {
            "occupation": occupation,
            "job_title": job_title(occupation, status, years_experience),
            "work_environment": env,
            "status": status,
        },
        "schedule": {
            "schedule_type": schedule_type,
            "work_hours": work_hours,
            "study_hours": list(study_hours) if study_hours else None,
            "days_off": days_off,  # weekday numbers, Monday = 0
            "weekly_hours": weekly,
            "can_listen_while_working": listen,
        },
        "work_characteristics": {
            "autonomy": autonomy,
            "work_stress": unit(rng, stress_mean + 0.2 * (n - 0.5), 5) if status not in ("retired",) else unit(rng, 0.15, 5),
            "cognitive_load": unit(rng, load, 6),
            "music_allowed": music_allowed,
        },
        "commute": {"mode": mode, "minutes_each_way": minutes},
        "exercise": {"days_per_week": days, "time_slot": slot, "exercise_type": types},
    }
    f.update(status=status, occupation=occupation, working=working, part_time=part_time, has_car=has_car,
             study_hours=study_hours, days_off=days_off, this_week_shift=this_week if o else schedule_type,
             enrolled_level=education["enrolled_in"], exerciser=days > 0)
