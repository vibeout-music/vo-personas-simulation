"""music_identity: taste is broad and varied, anchored to country, era and languages."""

from __future__ import annotations

from ..draft import Draft
from ..sampling import clamp, near, poisson, r2, signed, unit, weighted
from ..tables import (COUNTRIES, GENRE_LANGUAGE, GENRE_STYLE, GENRE_TEMPO, GENRES, INSTRUMENTAL_GENRES, THEMES, genre_arrival,
                      genre_birth, genre_reach)
from .emotional import bias

FEATURES = ["energy", "valence", "arousal", "danceability", "acousticness", "instrumentalness", "complexity", "intensity"]


def decade(year: int) -> str:
    return f"{year // 10 * 10}s"


def build(d: Draft) -> None:
    rng, f = d.rng, d.facts
    b = lambda k: bias(d, k)  # noqa: E731
    age = f["age"]
    sp = d.persona["stable_profile"]
    psy = d.persona["psychology"]
    openness = psy["big_five"]["openness"]

    # --- formative exposure: what was around while they grew up ---------------
    start, end = sp["formative_music_years"]
    country = f["country"]
    family_influence = d.persona["life_context"]["family_and_relationships"]["family"]["music_influence"]
    language = sp["languages"][0]["code"]
    reach = {g: genre_reach(g, country, language) for g in GENRES}
    around = {g: reach[g] for g in GENRES if genre_arrival(g, country) <= end}
    if family_influence > 0.5:  # parents' music: genres that were already old when they grew up
        for g in around:
            if genre_arrival(g, country) < start - 15:
                around[g] *= 2
    formative_genres = []
    for _ in range(rng.randint(2, 3)):
        formative_genres.append(weighted(rng, {g: w for g, w in around.items() if g not in formative_genres}))

    # --- genre affinities -----------------------------------------------------
    # Mean affinity rises for local and formative genres, and falls for genres
    # that arrived after their youth -- more with age, less if they are open.
    # These are only means: a 70-year-old trap fan is unlikely, not impossible.
    age_factor = clamp((age - 28) / 30)
    def mean_affinity(g: str) -> float:
        m = 0.05 + (0.3 if reach[g] >= 4 else -0.1 if reach[g] < 0.5 else 0) + (0.3 if g in formative_genres else 0)
        if genre_arrival(g, country) > end:
            m -= 0.35 * age_factor * (1.3 - 0.8 * openness)
        return m

    breadth = unit(rng, 0.3 + 0.3 * openness + b("taste_breadth"), 4)
    n_rated = max(4, min(16, 4 + poisson(rng, 2 + 8 * breadth)))
    candidates = {g: reach[g] * (0.6 + mean_affinity(g)) for g in GENRES}
    pool = list(formative_genres)
    while len(pool) < n_rated:
        pool.append(weighted(rng, {g: w for g, w in candidates.items() if g not in pool}))
    affinities = {g: signed(rng, mean_affinity(g), 2.5) for g in pool}
    for _ in range(rng.randint(1, min(3, len(pool)))):
        options = {g: 0.6 + mean_affinity(g) for g in pool if affinities[g] < 0.7}
        if not options:
            break
        affinities[weighted(rng, options)] = r2(0.7 + 0.28 * rng.random())
    favourites = [g for g, v in affinities.items() if v >= 0.7]
    affinities = dict(sorted(affinities.items(), key=lambda kv: -kv[1]))
    liked = [g for g, v in affinities.items() if v >= 0.5]

    style = {}
    for dim, genres in GENRE_STYLE.items():
        vals = [v for g, v in affinities.items() if g in genres]
        style[dim] = r2(clamp(0.5 + 0.5 * (sum(vals) / len(vals)) if vals else 0.5))

    # --- era, anchors, languages -------------------------------------------
    formative_decade = decade((start + end) // 2)
    nostalgia = d.get("emotional_profile.music_emotional_impact.nostalgia_proneness")
    preferred_era = formative_decade if rng.random() < 0.3 + 0.5 * nostalgia else "current"
    anchor_artists = []
    for g in rng.sample(liked, min(len(liked), rng.randint(1, 4))):
        # An artist cannot predate their genre.
        eras = [e for e in (formative_decade, decade(d.local.year)) if int(e[:4]) + 9 >= genre_birth(g)]
        era = rng.choice(eras)
        anchor_artists.append({"artist_id": f"art_{g}_{era}_{rng.randint(1, 300):03d}", "genre": g, "era": era})

    spoken = [lang["code"] for lang in sp["languages"] if lang["proficiency"] >= 0.5]
    comprehension = unit(rng, 0.5, 3)
    listening_languages = list(spoken)
    if comprehension < 0.5:  # happy to listen to lyrics they do not understand
        for g in liked:
            lang = GENRE_LANGUAGE.get(g)
            if lang and lang not in listening_languages:
                listening_languages.append(lang)
    if "en" not in listening_languages and comprehension < 0.7 and rng.random() < 0.6:
        listening_languages.append("en")  # global pop exposure
    if any(g in INSTRUMENTAL_GENRES for g in liked):
        listening_languages.append("instrumental")

    tempos = [GENRE_TEMPO[g] for g in liked if g in GENRE_TEMPO]
    tempo = round(sum(tempos) / len(tempos)) if tempos else 115
    tempo = [max(60, tempo - rng.randint(10, 25)), min(190, tempo + rng.randint(10, 25))]

    sophistication = unit(rng, 0.35 + b("sophistication") + 0.1 * openness, 3)
    musician = f["occupation"] == "musician"
    trained = musician or rng.random() < 0.2 + 0.6 * sophistication
    training = min(max(0, age - 5), rng.randint(1, max(1, round(4 + 16 * sophistication)))) if trained else 0
    if musician:
        training = max(training, min(age - 5, 3))

    guilty = [g for g, v in affinities.items() if 0.2 <= v < 0.6 and g not in favourites]
    guilty = rng.sample(guilty, min(len(guilty), rng.randint(0, 2)))

    functions = {
        "background": unit(rng, 0.5 + b("background"), 3),
        "focus": unit(rng, 0.35 + (0.2 if f["enrolled"] else 0) + 0.2 * (d.get("work_and_occupation.work_characteristics.music_allowed") is True), 3),
        "exercise": unit(rng, 0.2 + 0.1 * d.get("work_and_occupation.exercise.days_per_week"), 3),
        "relaxation": unit(rng, 0.55, 3),
        "emotion_processing": unit(rng, 0.4 + 0.2 * psy["big_five"]["neuroticism"] + b("emotion_processing"), 3),
        "social_connection": unit(rng, 0.35 + 0.2 * psy["big_five"]["extraversion"] + b("social"), 3),
        "identity_expression": unit(rng, 0.35 + (0.2 if age < 25 else 0) + b("identity"), 3),
        "killing_time": unit(rng, 0.45, 3),
    }

    d.persona["music_identity"] = {
        "importance_and_sophistication": {
            "identity_centrality": unit(rng, 0.45 + (0.15 if age < 25 else 0) + (0.3 if musician else 0) + b("identity"), 3),
            "musical_sophistication": sophistication,
            "active_musician": musician or (training >= 3 and rng.random() < 0.35),
            "training_years": training,
        },
        "genres_and_styles": {"genre_affinities": affinities, "style_dimensions": style},
        "taste_profile": {
            "taste_breadth": breadth,
            "preferred_era": preferred_era,
            "guilty_pleasures": guilty,
            "album_listener_vs_singles": unit(rng, 0.25 + 0.006 * age + 0.2 * sophistication, 4),  # 1 = albums
        },
        "anchor_artists": anchor_artists,
        "audio_features": {
            "preferred_tempo_bpm": tempo,
            "audio_feature_preferences": {
                "energy": {"ideal": near(rng, 0.3 + 0.4 * style["intense"], 0.12), "tolerance": unit(rng, 0.4, 3)},
                "valence": {"ideal": unit(rng, 0.5, 2.5), "tolerance": unit(rng, 0.4, 3)},
                "arousal": {"ideal": unit(rng, 0.5, 2.5), "tolerance": unit(rng, 0.4, 3)},
                "danceability": {"ideal": near(rng, 0.2 + 0.6 * style["contemporary"], 0.12), "tolerance": unit(rng, 0.4, 3)},
                "acousticness": {"ideal": near(rng, 0.2 + 0.3 * style["mellow"] + 0.3 * style["unpretentious"], 0.12), "tolerance": unit(rng, 0.4, 3)},
                "instrumentalness": {"ideal": near(rng, (0.5 if "instrumental" in listening_languages else 0.1), 0.12), "tolerance": unit(rng, 0.4, 3)},
                "complexity": {"ideal": near(rng, 0.2 + 0.4 * style["sophisticated"] + 0.3 * sophistication, 0.1), "tolerance": unit(rng, 0.4, 3)},
                "intensity": {"ideal": near(rng, 0.2 + 0.6 * style["intense"], 0.12), "tolerance": unit(rng, 0.4, 3)},
            },
        },
        "listening_dimensions": {
            "lyrics_vs_sound": unit(rng, 0.5, 3),  # 1 = lyrics matter most
            "lyrics": {
                "attention": unit(rng, 0.5, 3),
                "emotional_importance": unit(rng, 0.4 + 0.2 * psy["big_five"]["neuroticism"], 3),
                "language_comprehension_required": comprehension,
                "theme_affinities": {t: unit(rng, 0.5, 3) for t in rng.sample(THEMES, rng.randint(3, 6))},
            },
        },
        "sensory_and_discovery": {
            "frisson_sensitivity": unit(rng, 0.3 + 0.4 * openness, 4),
            "discovery": {
                "novelty_preference": unit(rng, 0.25 + 0.35 * openness + b("novelty"), 4),
                "popularity_bias": unit(rng, 0.55 + b("popularity") - 0.2 * (openness - 0.5), 3),
                "trend_sensitivity": unit(rng, 0.3 + (0.2 if age < 25 else 0) + 0.2 * psy["personality_traits"]["social_conformity"] + b("trend"), 4),
                "artist_loyalty": unit(rng, 0.45 + b("loyalty"), 4),
                "recommendation_trust": unit(rng, 0.5 + 0.1 * b("autoplay"), 4),
            },
        },
        "listening_functions": functions,
        "music_reward_sensitivity": {
            "musical_seeking": near(rng, 0.3 + 0.5 * sophistication, 0.12),
            "emotion_evocation": near(rng, d.get("emotional_profile.music_emotional_impact.musical_sensitivity"), 0.12),
            "mood_regulation": near(rng, functions["emotion_processing"], 0.12),
            "social_reward": near(rng, functions["social_connection"], 0.12),
            "sensory_motor": near(rng, 0.3 + 0.5 * style["contemporary"], 0.12),
        },
        "mood_regulation_affinity": {
            "entertainment": unit(rng, 0.55, 3),
            "revival": near(rng, functions["relaxation"], 0.15),
            "strong_sensation": near(rng, 0.2 + 0.6 * psy["personality_traits"]["sensation_seeking"], 0.12),
            "diversion": near(rng, functions["killing_time"], 0.15),
            "discharge": near(rng, 0.2 + 0.4 * style["intense"] + 0.2 * psy["big_five"]["neuroticism"], 0.12),
            "mental_work": near(rng, 0.2 + 0.5 * psy["cognitive_style"]["rumination_tendency"], 0.12),
            "solace": near(rng, functions["emotion_processing"], 0.15),
        },
        "formative_exposure": formative_genres,
        "listening_languages": listening_languages,
    }
