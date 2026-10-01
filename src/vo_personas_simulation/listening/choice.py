"""Choose the song a persona plays, and say why.

1. Candidates come from several sources whose share depends on the persona:
   their taste, nostalgia, what is popular, exploration, and songs they
   already know.
2. Each candidate is scored as a sum of named factors (taste, sound, mood,
   moment, nostalgia, popularity, novelty, familiarity, satiation, lyrics).
   Every factor is in [-1, 1] and has a weight that comes from the persona.
3. The choice is a softmax over the scores: consistent people almost always
   pick the best song, impulsive ones sometimes pick another.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime

from ..generation.sampling import clamp, weighted
from .history import effective_satiation

CANDIDATES = 200
SOUND_FEATURES = ("energy", "valence", "danceability", "acousticness", "instrumentalness")


class CatalogIndex:
    """The catalogue in memory, indexed for candidate generation."""

    def __init__(self, tracks: list[dict]):
        if not tracks:
            raise ValueError("the music catalogue is empty: run a harvest first")
        self.tracks = tracks
        self.by_id = {t["track_id"]: t for t in tracks}
        self.by_genre: dict[str, list[dict]] = {}
        for t in tracks:
            for g in t["genres"]:
                self.by_genre.setdefault(g, []).append(t)
        ranked = sorted((t for t in tracks if t["popularity"] is not None), key=lambda t: (-t["popularity"], t["track_id"]))
        self.popular = ranked[: max(20, len(ranked) // 10)] or tracks


@dataclass
class Choice:
    track: dict
    score: float
    contributions: dict
    reasons: list
    candidates: int


# --- candidates ------------------------------------------------------------------------


def candidates(p: dict, catalog: CatalogIndex, memory: dict, rng: random.Random) -> list[dict]:
    mi = p["music_identity"]
    affinities = mi["genres_and_styles"]["genre_affinities"]
    liked = {g: v for g, v in affinities.items() if v >= 0.3 and g in catalog.by_genre}
    start, end = p["stable_profile"]["formative_music_years"]
    nostalgic_genres = [g for g in (mi["formative_exposure"] + list(liked)) if g in catalog.by_genre]
    unexplored = [g for g in catalog.by_genre if g not in affinities]
    known = [catalog.by_id[t] for t, s in memory["tracks"].items() if s["learned_affinity"] > 0 and t in catalog.by_id]
    sources = {
        "taste": 0.45 if liked else 0,
        "nostalgia": (0.1 + 0.25 * p["emotional_profile"]["music_emotional_impact"]["nostalgia_proneness"]) if nostalgic_genres else 0,
        "popular": 0.05 + 0.2 * mi["sensory_and_discovery"]["discovery"]["popularity_bias"],
        "explore": (0.05 + 0.25 * mi["sensory_and_discovery"]["discovery"]["novelty_preference"]) if unexplored else 0,
        "known": (0.05 + 0.3 * p["routine_and_behavior"]["replay_and_habituation"]["repeat_propensity"]) if known else 0,
    }
    picked: dict[str, dict] = {}
    for _ in range(CANDIDATES * 3):
        if len(picked) >= CANDIDATES:
            break
        source = weighted(rng, sources)
        if source == "taste":
            pool = catalog.by_genre[weighted(rng, liked)]
        elif source == "nostalgia":
            genre_tracks = catalog.by_genre[rng.choice(nostalgic_genres)]
            pool = [t for t in genre_tracks if t["year"] and start - 2 <= t["year"] <= end + 2] or genre_tracks
        elif source == "popular":
            pool = catalog.popular
        elif source == "explore":
            pool = catalog.by_genre[rng.choice(unexplored)]
        else:
            pool = known
        track = rng.choice(pool)
        picked.setdefault(track["track_id"], track)
    return list(picked.values())


# --- factors --------------------------------------------------------------------------


def _taste(p, t):
    affinities = p["music_identity"]["genres_and_styles"]["genre_affinities"]
    rated = [(affinities[g], g) for g in t["genres"] if g in affinities]
    return max(rated) if rated else (0.0, None)


def factors(p: dict, t: dict, memory: dict, now: datetime, position: int) -> dict:
    """Named factors in [-1, 1] and their weights for one candidate track."""
    mi = p["music_identity"]
    intent = p["derived_listening_intent"]
    affect = p["mutable_state"]["current_affect"]
    feats, emo = t["audio_features"], t["emotion_profile"]
    discovery = mi["sensory_and_discovery"]["discovery"]
    replay = p["routine_and_behavior"]["replay_and_habituation"]
    out = {}

    taste, _ = _taste(p, t)
    out["taste"] = (taste, 1.0)

    prefs = mi["audio_features"]["audio_feature_preferences"]
    closeness = [math.exp(-((feats[f] - prefs[f]["ideal"]) / (0.1 + 0.4 * prefs[f]["tolerance"])) ** 2) for f in SOUND_FEATURES]
    lo, hi = mi["audio_features"]["preferred_tempo_bpm"]
    bpm = feats["tempo_bpm"]
    tempo_fit = 1.0 if lo <= bpm <= hi else max(-1.0, 1 - min(abs(bpm - lo), abs(bpm - hi)) / 30)
    out["sound_fit"] = (0.8 * (2 * sum(closeness) / len(closeness) - 1) + 0.2 * tempo_fit, 0.8)

    # Iso principle: the first song meets the current mood, later ones lead towards the target.
    target = affect if intent["regulation_strategy"] == "iso_then_shift" and position == 0 else intent["target_affect"]
    distance = math.hypot(emo["valence"] - target["valence"], emo["arousal"] - target["arousal"])
    out["mood"] = (clamp(1 - distance, -1, 1), 0.6 + 0.8 * mi["music_reward_sensitivity"]["mood_regulation"])

    pop = (t["popularity"] / 100) if t["popularity"] is not None else 0.5
    fn = intent["primary_function"]
    moment = {
        "exercise": 0.6 * (2 * feats["energy"] - 1) + 0.4 * clamp((bpm - 100) / 40, -1, 1),
        "focus": 1.2 * feats["instrumentalness"] - 0.6 + 0.6 * (0.5 - feats["energy"]),
        "relaxation": 1.4 * (0.5 - feats["energy"]) + 0.6 * (feats["acousticness"] - 0.5),
        "background": 1 - 2 * abs(feats["energy"] - 0.5),
        "social_connection": 1.4 * (feats["danceability"] - 0.5) + 0.6 * (pop - 0.5),
        "emotion_processing": 1 - abs(emo["valence"] - affect["valence"]),
        "identity_expression": 2 * taste - 1 if taste else 0.0,
        "killing_time": 2 * pop - 1,
    }[fn]
    out["moment"] = (clamp(moment, -1, 1), 0.8 + 0.8 * p["environmental_sensitivities"]["context_sensitivity"]["activity"])

    start, end = p["stable_profile"]["formative_music_years"]
    era = mi["taste_profile"]["preferred_era"]
    year = t["year"]
    nostalgia = 1.0 if year and start - 2 <= year <= end + 2 else 0.3 if year and era != "current" and f"{year // 10 * 10}s" == era else 0.0
    out["nostalgia"] = (nostalgia, 0.9 * p["emotional_profile"]["music_emotional_impact"]["nostalgia_proneness"])

    # Signed weights: a positive popularity_bias rewards hits, a negative one rewards the obscure.
    out["popularity"] = (2 * pop - 1, 1.6 * (discovery["popularity_bias"] - 0.5))

    track_state = memory["tracks"].get(t["track_id"])
    known_artist = any(memory["artists"].get(a["artist_id"], {}).get("familiarity", 0) > 0.2 for a in t["artists"])
    novelty = -1.0 if track_state else -0.3 if known_artist else 1.0
    out["novelty"] = (novelty, 1.2 * (discovery["novelty_preference"] - 0.5))

    if track_state:
        habituation = replay["habituation"]
        out["familiarity"] = (clamp(track_state["familiarity"] * track_state["learned_affinity"] * 2, -1, 1),
                              0.4 + 0.8 * replay["repeat_propensity"])
        out["satiation"] = (-min(1.0, effective_satiation(track_state, now, habituation)),
                            1.2 * (1 - 0.7 * replay["obsessive_replay"]))

    understood = "instrumental" in t["languages"] or any(l in mi["listening_languages"] for l in t["languages"])
    out["lyrics"] = (0.0 if understood else -1.0, 0.3 + 0.9 * mi["listening_dimensions"]["lyrics"]["language_comprehension_required"])
    return out


# --- explanations ------------------------------------------------------------------------


def explain(name: str, p: dict, t: dict, value: float) -> str:
    feats = t["audio_features"]
    intent = p["derived_listening_intent"]
    activity = p["current_context"]["activity_and_location"]["activity"]
    if name == "taste":
        affinity, genre = _taste(p, t)
        return f"loves {genre} (affinity {affinity})"
    if name == "sound_fit":
        return f"sounds like what they like (energy {feats['energy']}, danceability {feats['danceability']}, {feats['tempo_bpm']} bpm)"
    if name == "mood":
        if intent["regulation_strategy"] == "iso_then_shift":
            return "meets their current mood first, to lift it gradually (iso principle)"
        return f"fits the mood they want ({intent['regulation_strategy'].replace('_', ' ')})"
    if name == "moment":
        doing = "trying to sleep" if activity == "sleeping" else activity.replace("_", " ")
        return f"right for {intent['primary_function'].replace('_', ' ')} while {doing}"
    if name == "nostalgia":
        return f"from their formative years ({t['year']})" if value >= 1 else f"from the era they prefer ({t['year']})"
    if name == "popularity":
        return f"a popular track ({t['popularity']}) and they follow what is popular" if value > 0 else "an under-the-radar track, as they like"
    if name == "novelty":
        return "a new artist for them, and they like discovering" if value > 0 else "an artist they already know and trust"
    if name == "familiarity":
        return "a song they already know and like"
    if name == "satiation":
        return "they have not heard it for a while"
    return "in a language they understand"


# --- choice ------------------------------------------------------------------------------


def choose(p: dict, catalog: CatalogIndex, memory: dict, rng: random.Random, now: datetime, position: int = 0) -> Choice:
    pool = candidates(p, catalog, memory, rng)
    scored = []
    for t in pool:
        contributions = {name: value * weight for name, (value, weight) in factors(p, t, memory, now, position).items()}
        scored.append((sum(contributions.values()), t, contributions))
    behaviour = p["platform_and_devices"]["platform_behavior"]
    temperature = 0.12 + 0.5 * behaviour["behavioural_noise"] + 0.25 * (1 - behaviour["choice_consistency"])
    best = max(s for s, _, _ in scored)
    weights = [math.exp((s - best) / temperature) for s, _, _ in scored]
    score, track, contributions = scored[rng.choices(range(len(scored)), weights=weights)[0]]

    # Reasons: what set this song apart from the other candidates, not what they all share.
    all_factors = factors(p, track, memory, now, position)
    average = {n: sum(c.get(n, 0.0) for _, _, c in scored) / len(scored) for n in contributions}
    edge = sorted(((contributions[n] - average[n], n) for n in contributions if contributions[n] > 0), reverse=True)
    reasons = [{"factor": n, "contribution": round(contributions[n], 2), "edge_over_others": round(e, 2),
                "detail": explain(n, p, track, all_factors[n][0])} for e, n in edge[:3] if e > 0]
    if not reasons:  # an average pick: its strongest factor is the honest reason
        c, n = max((c, n) for n, c in contributions.items())
        reasons = [{"factor": n, "contribution": round(c, 2), "edge_over_others": 0.0, "detail": explain(n, p, track, all_factors[n][0])}]
    return Choice(track=track, score=round(score, 3), contributions={k: round(v, 3) for k, v in contributions.items()},
                  reasons=reasons, candidates=len(pool))
