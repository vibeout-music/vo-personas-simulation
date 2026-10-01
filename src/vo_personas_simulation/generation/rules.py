"""Shape and coherence checks run on every generated persona."""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

from .draft import age_on, life_stage_for
from .sampling import clamp
from .sections.context import in_window
from .sections.life import event_allowed
from .sections.psychology import goal_allowed
from .tables import (DAILY_EVENTS, EDUCATION_MIN_COMPLETION_AGE, EDUCATION_NEXT, EDUCATION_RANK, GENRE_LANGUAGE,
                     OCCUPATIONS, PRECIPITATING, genre_arrival, genre_birth)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "persona-unified-schema.json"

# Fields that may legitimately be null (the coherence rules below say when).
NULLABLE = {
    "metadata.$schema", "metadata._llm_model",
    "stable_profile.education.enrolled_in",
    "life_context.family_and_relationships.romantic_relationship.satisfaction",
    "work_and_occupation.occupation.job_title",
    "work_and_occupation.schedule.work_hours",
    "work_and_occupation.schedule.study_hours",
    "work_and_occupation.schedule.can_listen_while_working",
    "work_and_occupation.work_characteristics.music_allowed",
    "work_and_occupation.exercise.time_slot", "work_and_occupation.exercise.exercise_type",
    "current_context.event_of_the_day.event_type", "current_context.event_of_the_day.description",
    "current_context.event_of_the_day.valence_impact", "current_context.event_of_the_day.arousal_impact",
    "current_context.special_dates.holiday_or_special",
    "current_context.song_of_the_moment",
    "mutable_state.active_pressures.active_insecurity",
}

WORKING = ("employed", "self_employed", "student_working")
PARTNER_ARRANGEMENTS = ("with_partner", "with_partner_and_children")


@lru_cache(maxsize=1)
def load_template(path: Path = SCHEMA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_shape(persona: dict, template: dict | None = None) -> list[str]:
    """The persona must have exactly the schema's keys, and no unexpected nulls."""
    errors = []

    def walk(t: dict, p: dict, path: str):
        if not isinstance(p, dict):
            errors.append(f"{path or '<root>'}: expected an object")
            return
        for key in t.keys() - p.keys():
            errors.append(f"missing field {path}{key}")
        for key in p.keys() - t.keys():
            errors.append(f"unexpected field {path}{key}")
        for key in t.keys() & p.keys():
            full = f"{path}{key}"
            if isinstance(t[key], dict) and t[key]:
                walk(t[key], p[key], full + ".")
            elif p[key] is None and full not in NULLABLE:
                errors.append(f"null value in {full}")

    walk(template or load_template(), persona, "")
    return errors


def check_coherence(p: dict) -> list[str]:
    errors = []

    def rule(ok: bool, message: str):
        if not ok:
            errors.append(message)

    sp, life, work = p["stable_profile"], p["life_context"], p["work_and_occupation"]
    ctx, state = p["current_context"], p["mutable_state"]
    age = sp["demographics"]["age"]
    local = datetime.fromisoformat(ctx["temporal"]["local_time"])
    birth = date.fromisoformat(sp["demographics"]["birth_date"])
    status = work["occupation"]["status"]
    occupation = work["occupation"]["occupation"]
    relationship = life["family_and_relationships"]["romantic_relationship"]["status"]
    arrangement = life["living_situation"]["living_arrangement"]
    children = life["family_and_relationships"]["children"]
    minors = [c for c in children if c["age"] < 18]
    devices = p["platform_and_devices"]["devices"]
    activity = ctx["activity_and_location"]["activity"]
    location = ctx["activity_and_location"]["location_type"]
    audio = ctx["technical_setup"]["audio_output"]

    # --- identity -------------------------------------------------------------
    rule(age_on(birth, local.date()) == age, "age does not match birth_date")
    rule(life_stage_for(age) == sp["demographics"]["life_stage"], "life_stage does not match age")
    rule(sp["formative_music_years"] == [birth.year + 12, min(birth.year + 22, local.year)], "formative_music_years inconsistent with birth year")
    rule(sum(lang["is_primary"] for lang in sp["languages"]) == 1, "exactly one primary language")

    # --- education: a trajectory, not a label ------------------------------------
    edu = sp["education"]
    highest, enrolled = edu["highest_completed"], edu["enrolled_in"]
    rule(age >= EDUCATION_MIN_COMPLETION_AGE[highest], f"{highest} cannot be completed at {age}")
    rule(enrolled is None or enrolled in EDUCATION_NEXT[highest], f"enrolled in {enrolled} after completing {highest}")
    if age < 16:
        rule(highest == "primary" and enrolled == "secondary", "under 16 must be in secondary school")
    rule((enrolled is not None) == status.startswith("student"), "student status must match enrolment")

    # --- minors -----------------------------------------------------------------
    if age < 18:
        rule(arrangement == "with_parents", "minor not living with parents")
        rule(not children, "minor with children")
        rule(relationship in ("single", "dating"), f"minor with relationship status {relationship}")
        rule("car_audio" not in devices, "minor owns a car")
        rule(status in ("student", "student_working") and work["schedule"]["weekly_hours"] <= 32, "minor working full time")
        rule(location != "bar", "minor in a bar")

    # --- family and household ------------------------------------------------------
    for child in children:
        rule(age - child["age"] >= 16, "parent less than 16 years older than child")
    if arrangement in PARTNER_ARRANGEMENTS:
        rule(relationship in ("cohabiting", "married"), f"{arrangement} while {relationship}")
    rule(arrangement != "with_partner_and_children" or minors, "with_partner_and_children without minor children")
    rule(arrangement != "single_parent" or (minors and relationship not in ("cohabiting", "married")), "invalid single_parent household")
    partnered = relationship in ("dating", "cohabiting", "married")
    rule((life["family_and_relationships"]["romantic_relationship"]["satisfaction"] is None) != partnered, "relationship satisfaction without a partner")
    for ev in life["life_events"]["active_life_events"]:
        # Judge an event by the age the persona had when it started.
        started = date.fromisoformat(ev["started_on"])
        rule(started <= local.date(), f"life event {ev['event_type']} starts in the future")
        age_then = age_on(birth, started)
        facts = {"age": age_then, "enrolled": enrolled is not None, "status": status}
        rule(event_allowed(ev["event_type"], facts, life), f"life event {ev['event_type']} does not fit the persona")

    # --- work -------------------------------------------------------------------------
    if occupation in OCCUPATIONS:
        o = OCCUPATIONS[occupation]
        rule(o["ages"][0] <= age <= o["ages"][1], f"{occupation} impossible at {age}")
        rule(EDUCATION_RANK[highest] >= o["edu"], f"{occupation} requires more education than {highest}")
    rule(status != "retired" or age >= 55, "retired too young")
    non_working = status in ("retired", "unemployed", "homemaker")
    rule(not non_working or work["schedule"]["weekly_hours"] == 0, "non-working person with weekly hours")
    rule((work["schedule"]["can_listen_while_working"] is None) == non_working, "can_listen_while_working vs status")
    rule((work["occupation"]["job_title"] is None) == (status not in WORKING), "job_title vs status")
    rule((work["schedule"]["study_hours"] is None) == (enrolled is None), "study_hours vs enrolment")
    days_off = work["schedule"]["days_off"]
    rule(len(set(days_off)) == 2 and all(0 <= x <= 6 for x in days_off), "days_off must be two distinct weekdays")
    commute = work["commute"]
    rule((commute["mode"] == "none") == (commute["minutes_each_way"] == 0), "commute mode vs minutes")
    rule(commute["mode"] != "car" or "car_audio" in devices, "commutes by car without a car")
    ex = work["exercise"]
    rule((ex["days_per_week"] == 0) == (ex["time_slot"] is None), "exercise days vs time slot")

    # --- goals --------------------------------------------------------------------------
    goal_facts = {"age": age, "status": status, "has_children": bool(children), "partnered": partnered,
                  "enrolled": enrolled is not None, "enrolled_level": enrolled}
    for goal in p["psychology"]["goals_and_ambitions"]["goals"]:
        # Goals are stable: a birthday during a simulation does not cancel them.
        rule(goal_allowed(goal, goal_facts) or goal_allowed(goal, {**goal_facts, "age": age - 1}),
             f"goal {goal} does not fit the persona")

    # --- music --------------------------------------------------------------------------
    music = p["music_identity"]
    affinities = music["genres_and_styles"]["genre_affinities"]
    rule(max(affinities.values()) >= 0.7, "no favourite genre")
    for artist in music["anchor_artists"]:
        rule(affinities.get(artist["genre"], -1) >= 0.5, "anchor artist from a genre they do not like")
        rule(int(artist["era"][:4]) + 9 >= genre_birth(artist["genre"]), f"anchor artist predates {artist['genre']}")
    for g in music["formative_exposure"]:
        rule(genre_arrival(g, sp["residency"]["country"]) <= sp["formative_music_years"][1],
             f"formative exposure to {g} before it reached {sp['residency']['country']}")
    for g in music["taste_profile"]["guilty_pleasures"]:
        rule(0.2 <= affinities.get(g, -1) < 0.6, "guilty pleasure outside the mid-affinity range")
    formative_decade = f"{(sp['formative_music_years'][0] + sp['formative_music_years'][1]) // 2 // 10 * 10}s"
    rule(music["taste_profile"]["preferred_era"] in (formative_decade, "current"), "preferred era unrelated to formative years")
    imp = music["importance_and_sophistication"]
    rule(imp["training_years"] <= max(0, age - 5), "training_years exceeds age")
    rule(occupation != "musician" or (imp["active_musician"] and imp["training_years"] > 0), "musician without training")
    spoken = {lang["code"] for lang in sp["languages"] if lang["proficiency"] >= 0.5}
    liked_langs = {GENRE_LANGUAGE[g] for g, v in affinities.items() if v >= 0.5 and g in GENRE_LANGUAGE}
    comprehension = music["listening_dimensions"]["lyrics"]["language_comprehension_required"]
    for lang in music["listening_languages"]:
        if lang in spoken or lang == "instrumental":
            continue
        rule(comprehension < 0.7 and (lang == "en" or lang in liked_langs), f"listens in {lang} without understanding it")

    # --- devices and platform --------------------------------------------------------------
    has_car = "car_audio" in devices
    spaces = p["environmental_sensitivities"]["listening_spaces"]["preferred_listening_spaces"]
    rule(has_car or spaces["car_speakers"] == 0, "car speaker preference without a car")
    tier = p["platform_and_devices"]["tier"]
    rule(tier != "student" or (enrolled and age >= 18), "student plan without being a student")
    rule(tier != "duo" or arrangement in PARTNER_ARRANGEMENTS, "duo plan without a partner at home")
    rule(tier != "family" or arrangement not in ("alone", "shared", "with_partner"), "family plan without family at home")
    rule(tier != "premium" or age >= 18, "minor paying an individual plan")

    # --- context ----------------------------------------------------------------------------
    rule(ctx["technical_setup"]["device"] in devices, "context device not owned")
    rule((audio == "car_audio") == (location == "car"), "car_audio vs location")
    rule(audio != "smart_speaker" or "smart_speaker" in devices, "smart speaker output without owning one")
    rule(location in ("home", "friend_home") or (audio not in ("home_speakers", "smart_speaker")
                                               and ctx["technical_setup"]["device"] not in ("tv", "console", "desktop")), "home equipment outside home")
    if activity == "working":
        rule(status in WORKING and in_window(local.hour, work["schedule"]["work_hours"]), "working outside working hours")
    if activity == "commuting":
        rule(commute["mode"] != "none", "commuting without a commute")
    if location == "school":
        rule(enrolled is not None or OCCUPATIONS.get(occupation, {}).get("loc") == "school", "at school without studying or working there")
    weather = ctx["environmental_conditions"]["weather"]
    rule(weather["condition"] in PRECIPITATING or weather["precipitation"] == 0, "precipitation without a precipitating condition")
    rule(weather["condition"] != "snow" or weather["temperature_c"] <= 3, "snow in warm weather")
    special = ctx["special_dates"]["holiday_or_special"]
    rule((special == "birthday") == (birth.strftime("%m-%d") == local.strftime("%m-%d")), "birthday flag vs birth date")
    rule((ctx["temporal"]["day_type"] == "weekend") == (local.weekday() >= 5 and ctx["temporal"]["day_type"] != "holiday"), "day_type vs date")
    event = ctx["event_of_the_day"]["event_type"]
    if event:
        req = DAILY_EVENTS[event][3]
        rule({None: True, "partner": partnered, "employed": status in WORKING, "enrolled": enrolled is not None,
              "family": arrangement in ("with_parents", "with_family", "with_partner_and_children", "single_parent"),
              "car": commute["mode"] == "car", "transit": commute["mode"] in ("public_transport", "school_bus"),
              "young_child": any(c["age"] < 12 for c in minors), "adult": age >= 18,
              "exerciser": ex["days_per_week"] > 0}[req], f"event {event} does not fit the persona")

    # --- state and intent ---------------------------------------------------------------------
    phys = state["physiological_state"]
    rule(abs(phys["energy"] + phys["fatigue"] - 1) <= 0.3, "energy and fatigue not opposed")
    expected_debt = max(0.0, p["neurobiology"]["sleep_characteristics"]["average_sleep_hours"] - phys["sleep"]["hours_last_night"])
    rule(abs(phys["sleep"]["sleep_debt"] - expected_debt) <= 0.11, "sleep_debt inconsistent")
    rule(activity != "sleeping" or phys["energy"] <= 0.25, "high energy while sleeping")
    intent = p["derived_listening_intent"]
    rule(intent["primary_function"] != "exercise" or activity == "exercising", "exercise function outside exercise")
    rule(audio != "none" or intent["listen_probability"] <= 0.2, "high listen probability without audio output")
    rule(clamp(intent["listen_probability"]) == intent["listen_probability"], "listen_probability out of range")
    return errors


def validate(persona: dict) -> list[str]:
    return check_shape(persona) + check_coherence(persona)
