"""Estimated audio features, emotion and language for catalogue tracks.

Spotify no longer serves audio features to new apps, so they are estimated
from the track's genres, era and popularity. The noise is seeded with the
track id, so the same track always gets the same values; every estimate is
stored with features_source = "estimated".
"""

from __future__ import annotations

import hashlib
import random

from ..generation.sampling import clamp, r2
from ..generation.tables import (COUNTRIES, GENRE_AUDIO, GENRE_LANGUAGE, GENRE_ORIGIN, GENRE_TEMPO,
                                 INSTRUMENTAL_GENRES)

FEATURES = ("energy", "valence", "danceability", "acousticness", "instrumentalness")


def _rng(track_id: str) -> random.Random:
    return random.Random(int.from_bytes(hashlib.sha256(track_id.encode()).digest()[:8], "big"))


def estimate_features(track_id: str, genres: list[str], year: int | None, popularity: int | None) -> dict:
    rng = _rng(track_id)
    known = [g for g in genres if g in GENRE_AUDIO] or ["pop"]
    means = [sum(GENRE_AUDIO[g][i] for g in known) / len(known) for i in range(len(FEATURES))]
    feats = dict(zip(FEATURES, means))
    if year:  # older recordings are more acoustic and less loud
        feats["acousticness"] += 0.004 * max(0, 2000 - year)
        feats["energy"] -= 0.002 * max(0, 2000 - year)
    if popularity is not None:  # hits lean danceable and upbeat
        feats["danceability"] += 0.1 * (popularity / 100 - 0.5)
        feats["valence"] += 0.05 * (popularity / 100 - 0.5)
    feats = {k: r2(clamp(v + rng.gauss(0, 0.1), 0.02, 0.98)) for k, v in feats.items()}
    tempos = [GENRE_TEMPO[g] for g in known if g in GENRE_TEMPO]
    feats["tempo_bpm"] = round(clamp((sum(tempos) / len(tempos) if tempos else 115) + rng.gauss(0, 12), 55, 200))
    return feats


def emotion_profile(features: dict) -> dict:
    """Valence/arousal of the music in [-1, 1], derived from the estimated features."""
    arousal = 0.7 * features["energy"] + 0.3 * clamp((features["tempo_bpm"] - 60) / 120)
    return {"valence": r2(2 * features["valence"] - 1), "arousal": r2(2 * arousal - 1)}


def estimate_languages(genres: list[str], market: str | None, instrumentalness: float) -> list[str]:
    langs = {GENRE_LANGUAGE[g] for g in genres if g in GENRE_LANGUAGE}
    if not langs and instrumentalness >= 0.6 and any(g in INSTRUMENTAL_GENRES for g in genres):
        return ["instrumental"]
    if not langs and market in COUNTRIES:
        local = [g for g in genres if g in COUNTRIES[market]["genres"] or market in GENRE_ORIGIN[g][1]]
        if local:
            langs.add(COUNTRIES[market]["lang"])
    return sorted(langs or {"en"})
