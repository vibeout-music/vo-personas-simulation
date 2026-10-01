"""psychology: personality, values, goals, concerns, coping.

Personality is deliberately varied; only well-established correlations are
encoded. Goals are filled after work and life, because they depend on them.
"""

from __future__ import annotations

from ..draft import Draft
from ..sampling import clamp, near, r2, unit, weighted
from ..tables import AMBITIONS, CONCERNS, GOALS_BY_AMBITION

REGULATION_GOALS = ["calm_down", "cheer_up", "energize", "process_emotions", "focus", "feel_understood"]


def build_core(d: Draft) -> None:
    rng = d.rng
    o, c, e, a, n = (unit(rng, 0.55, 4), unit(rng, 0.5, 4), unit(rng, 0.5, 4), unit(rng, 0.55, 4), unit(rng, 0.5, 4))
    sensation = unit(rng, 0.3 + 0.4 * o, 4)
    impulsivity = near(rng, 0.5 * sensation + 0.5 * (1 - c), 0.08)

    style = weighted(rng, {
        "problem_focused": 1 + 2 * c,
        "emotion_focused": 1 + n,
        "social_support_seeking": 0.5 + a + e,
        "avoidant": 0.3 + 2 * n * (1 - c),
    })
    strategy = weighted(rng, {
        "reappraisal": 0.5 + 1.5 * o * (1 - n),
        "distraction": 1,
        "suppression": 0.3 + (1 - e) * (1 - o),
        "rumination": 0.2 + 2 * n,
        "music_listening": 1,
    })
    goals = ["calm_down"] if n > 0.6 else []
    goals += [g for g in rng.sample(REGULATION_GOALS, rng.randint(1, 3)) if g not in goals]

    d.persona["psychology"] = {
        "big_five": {"openness": o, "conscientiousness": c, "extraversion": e, "agreeableness": a, "neuroticism": n},
        "personality_traits": {
            "sensation_seeking": sensation,
            "cognitive_style_E_S": unit(rng, 0.5, 4),  # 0 = empathising, 1 = systemising
            "self_esteem": unit(rng, 0.75 - 0.45 * n, 8),
            "locus_of_control": rng.choices(["internal", "external"], weights=[1 - n * 0.5, 0.3 + n * 0.5])[0],
            "impulsivity": impulsivity,
            "optimism": unit(rng, 0.7 - 0.4 * n + 0.1 * e, 7),
            "social_conformity": unit(rng, 0.55 - 0.25 * o + 0.15 * a, 4),
        },
        "cognitive_style": {
            "novelty_seeking": near(rng, 0.3 * sensation + 0.7 * o, 0.1),
            "uncertainty_tolerance": unit(rng, 0.6 - 0.35 * n + 0.1 * o, 6),
            "rumination_tendency": unit(rng, 0.2 + 0.6 * n, 5),
        },
        "values": {k: unit(rng, 0.5, 3) for k in ["achievement", "belonging", "autonomy", "security", "exploration", "social_status", "meaning"]},
        "goals_and_ambitions": {"ambitions": None, "goals": None, "mindset": unit(rng, 0.5, 3)},  # 1 = growth mindset
        "insecurities_and_fears": {"concerns": None},
        "coping_mechanisms": {
            "coping_mechanism_style": style,
            "regulation_strategy": strategy,
            "primary_regulation_goals": goals,
        },
    }


def goal_allowed(goal: str, f: dict) -> bool:
    """Goals must fit the person's situation."""
    age, status = f["age"], f["status"]
    employed = status in ("employed", "self_employed", "student_working")
    rules = {
        "get_promoted": employed and age >= 20,
        "change_jobs": status != "student" and age >= 18,
        "start_a_business": age >= 18,
        "start_a_family": age >= 22 and not f["has_children"],
        "spend_more_time_with_family": f["has_children"] or age < 18 or f["partnered"],
        "finish_degree": f["enrolled_level"] in ("vocational", "bachelor", "master", "doctorate"),
        "pass_exams": f["enrolled"],
        "buy_a_home": age >= 22,
        "pay_off_debt": age >= 18,
    }
    return rules.get(goal, True)


def build_goals(d: Draft) -> None:
    rng, f = d.rng, d.facts
    psy = d.persona["psychology"]
    weights = {a: 1.0 for a in AMBITIONS}
    if f["enrolled"]:
        weights["education"] = 3
    if f["has_children"]:
        weights["family"] = 3
    if f["age"] >= 60:
        weights["health"] = 3
        weights["career"] = 0.3
    weights["recognition"] = 0.5 + psy["values"]["social_status"]
    ambitions = []
    for _ in range(rng.randint(1, 4)):
        pick = weighted(rng, {k: v for k, v in weights.items() if k not in ambitions})
        ambitions.append(pick)

    goals = []
    for amb in ambitions:
        options = [g for g in GOALS_BY_AMBITION[amb] if goal_allowed(g, f)]
        if options:
            goals.append(rng.choice(options))

    n = psy["big_five"]["neuroticism"]
    concern_w = {c: 1.0 for c in CONCERNS}
    concern_w["money"] = 0.5 + 2 * d.get("life_context.financial.financial_pressure")
    concern_w["loneliness"] = 0.5 + 2 * d.get("life_context.social_connections.baseline_loneliness")
    concern_w["career"] = 1.5 if f["status"] in ("unemployed", "employed", "self_employed") else 0.3
    concern_w["health"] = 0.5 + (f["age"] / 50)
    concern_w["appearance"] = 1.8 if f["age"] < 25 else 0.6
    concerns = []
    for _ in range(rng.randint(1, 2 + round(2 * n))):
        concerns.append(weighted(rng, {k: v for k, v in concern_w.items() if k not in concerns}))

    psy["goals_and_ambitions"]["ambitions"] = ambitions
    psy["goals_and_ambitions"]["goals"] = list(dict.fromkeys(goals))
    psy["insecurities_and_fears"]["concerns"] = concerns
