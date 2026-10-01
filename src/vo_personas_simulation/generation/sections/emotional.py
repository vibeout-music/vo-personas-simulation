"""emotional_profile: baseline affect, dynamics and regulation."""

from __future__ import annotations

from ..draft import Draft
from ..sampling import clamp, near, r2, signed, unit
from ..tables import ARCHETYPE_BIAS


def bias(d: Draft, key: str) -> float:
    return sum(w * ARCHETYPE_BIAS[a].get(key, 0.0) for a, w in d.facts["archetype_mix"].items())


def build(d: Draft) -> None:
    rng = d.rng
    b5 = d.persona["psychology"]["big_five"]
    n, e = b5["neuroticism"], b5["extraversion"]
    lc = d.persona["life_context"]

    stress = r2(clamp(0.1 + 0.3 * n + 0.25 * d.get("work_and_occupation.work_characteristics.work_stress")
                      + 0.2 * lc["financial"]["financial_pressure"] + 0.15 * lc["living_situation"]["caregiving_load"]
                      + rng.gauss(0, 0.08)))
    volatility = unit(rng, 0.2 + 0.6 * n, 5)

    d.persona["emotional_profile"] = {
        "baseline": {
            "valence": signed(rng, 0.25 - 0.5 * n + 0.2 * e, 5),  # trait level; life events move the current state
            "arousal": signed(rng, 0.15 * (e - 0.5) + 0.1 * (stress - 0.5), 4),
            "dominance": signed(rng, 0.15 - 0.3 * n + 0.5 * (d.get("psychology.personality_traits.self_esteem") - 0.5), 8),
            "stress": stress,
        },
        "dynamics": {
            "volatility": volatility,
            "inertia": near(rng, 0.8 - 0.5 * volatility, 0.1),
            "recovery_rate": unit(rng, 0.7 - 0.4 * n, 5),
            "emotion_clarity": unit(rng, 0.55 - 0.15 * n, 3),
            "emotion_expression": unit(rng, 0.3 + 0.4 * e, 4),
        },
        "regulation": {"iso_principle_adherence": unit(rng, 0.45 + bias(d, "iso"), 4)},
        "music_emotional_impact": {
            "musical_sensitivity": unit(rng, 0.5 + bias(d, "musical_sensitivity"), 3),
            "nostalgia_proneness": unit(rng, 0.35 + 0.004 * d.facts["age"] + 0.1 * n, 4),
        },
    }
