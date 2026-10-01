"""One listening moment for one persona: rebuild the moment, choose songs, play them, remember them."""

from __future__ import annotations

import math
import random
import uuid
from datetime import datetime, timedelta

from ..generation.moment import build_moment
from ..generation.sampling import clamp, derive_seed, r2
from .choice import CatalogIndex, choose
from .history import ListeningHistory, iso, remember


def play(p: dict, choice, rng: random.Random) -> tuple[str, int, bool]:
    """What happens once the song starts: skipped or completed, and liked or not."""
    behaviour = p["routine_and_behavior"]
    utility = math.tanh(choice.score / 2)  # how good this pick is for them, in (-1, 1)
    duration = choice.track["duration_ms"] or 200_000
    p_skip = clamp(behaviour["skip_behavior"]["skip_rate"] * (1 - 0.6 * utility) + 0.1 * p["mutable_state"]["music_satiation"], 0.02, 0.95)
    if rng.random() < p_skip:
        patience = behaviour["skip_behavior"]["skip_patience_seconds"] * 1000
        return "skipped", int(min(duration, patience * rng.uniform(0.3, 1.2))), False
    liked = rng.random() < clamp(behaviour["feedback_behavior"]["like_rate"] * (0.5 + utility))
    listened = int(duration * rng.uniform(behaviour["replay_and_habituation"]["completion_bias"] * 0.1 + 0.9, 1.0))
    return "completed", listened, liked


def song_summary(choice, listen_probability: float) -> dict:
    t = choice.track
    return {
        "track_id": t["track_id"],
        "spotify_url": t["spotify_url"],
        "title": t["title"],
        "artists": [a["name"] for a in t["artists"]],
        "album": t["album"],
        "year": t["year"],
        "genres": t["genres"],
        "score": choice.score,
        "listen_probability": listen_probability,
        "features_source": t["features_source"],
        "reasons": choice.reasons,
    }


def simulate_persona(persona: dict, when: datetime, *, run_id: str, seed: int, catalog: CatalogIndex,
                     history: ListeningHistory, listens: int = 1, respect_listen_probability: bool = False) -> dict:
    pid = persona["metadata"]["persona_id"]
    moment = build_moment(persona, when, derive_seed(seed, pid, iso(when), "moment"))
    rng = random.Random(derive_seed(seed, pid, iso(when), "listen"))
    ctx, state, intent = moment["current_context"], moment["mutable_state"], moment["derived_listening_intent"]
    line = {
        "run_id": run_id,
        "persona_id": pid,
        "simulated_at": iso(when),
        "local_time": ctx["temporal"]["local_time"],
        "context": {
            "day_type": ctx["temporal"]["day_type"], "time_of_day": ctx["temporal"]["time_of_day"],
            "activity": ctx["activity_and_location"]["activity"], "location": ctx["activity_and_location"]["location_type"],
            "company": ctx["social_context"]["social_company"], "device": ctx["technical_setup"]["device"],
            "audio_output": ctx["technical_setup"]["audio_output"],
            "weather": ctx["environmental_conditions"]["weather"]["condition"],
            "event_of_the_day": ctx["event_of_the_day"]["event_type"],
        },
        "state": {"valence": state["current_affect"]["valence"], "arousal": state["current_affect"]["arousal"],
                  "energy": state["physiological_state"]["energy"], "stress": state["physiological_state"]["stress"]},
        "intent": {"listen_probability": intent["listen_probability"], "primary_function": intent["primary_function"],
                   "regulation_strategy": intent["regulation_strategy"]},
        "listened": True,
        "listens": [],
        "song_of_the_moment": None,
    }
    if respect_listen_probability and rng.random() >= intent["listen_probability"]:
        line["listened"] = False  # not a moment for music (asleep, no audio, busy...)
        return line

    memory = history.load_memory(pid)
    habituation = moment["routine_and_behavior"]["replay_and_habituation"]["habituation"]
    sensitivity = moment["emotional_profile"]["music_emotional_impact"]["musical_sensitivity"]
    t = when
    for position in range(listens):
        choice = choose(moment, catalog, memory, rng, t, position)
        outcome, listened_ms, liked = play(moment, choice, rng)
        remember(memory, choice.track, outcome=outcome, liked=liked, when=t, habituation=habituation)
        history.record_listen(
            event_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{run_id}/{pid}/{position}")), run_id=run_id, persona_id=pid,
            when=t, local_time=ctx["temporal"]["local_time"], position=position, track=choice.track, outcome=outcome,
            listened_ms=listened_ms, liked=liked, context=line["context"], state=dict(line["state"]),
            reasons=choice.reasons, memory=memory)
        line["listens"].append({"position": position, **song_summary(choice, intent["listen_probability"]),
                                "outcome": outcome, "listened_ms": listened_ms, "liked": liked})
        if outcome == "completed":
            # Music moves the mood towards the song's emotion, more for sensitive listeners.
            affect, emo = state["current_affect"], choice.track["emotion_profile"]
            pull = 0.25 * sensitivity
            affect["valence"] = r2(affect["valence"] + (emo["valence"] - affect["valence"]) * pull)
            affect["arousal"] = r2(affect["arousal"] + (emo["arousal"] - affect["arousal"]) * pull)
            line["song_of_the_moment"] = line["listens"][-1]
        state["music_satiation"] = r2(clamp(state["music_satiation"] + 0.05, 0.02, 0.98))
        t = t + timedelta(milliseconds=listened_ms)
    if line["song_of_the_moment"] is None:  # everything was skipped: the last attempt is what was on
        line["song_of_the_moment"] = line["listens"][-1]
    line["state_after"] = {"valence": state["current_affect"]["valence"], "arousal": state["current_affect"]["arousal"]}
    return line
