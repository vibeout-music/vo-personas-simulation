"""derived_listening_intent and memory_references, computed from state and context."""

from __future__ import annotations

from ..draft import Draft
from ..sampling import clamp, r2, weighted
from ..tables import ACTIVITY_LISTENING

ACTIVITY_FUNCTIONS = {
    "exercising": {"exercise": 3},
    "working": {"focus": 2, "background": 1},
    "studying": {"focus": 3},
    "socializing": {"social_connection": 3},
    "commuting": {"killing_time": 1.5, "background": 1, "emotion_processing": 1},
    "winding_down": {"relaxation": 2, "emotion_processing": 1},
    "relaxing": {"relaxation": 1.5, "emotion_processing": 1, "identity_expression": 1},
}


def build(d: Draft) -> None:
    rng = d.rng
    p = d.persona
    ctx, state = p["current_context"], p["mutable_state"]
    activity = ctx["activity_and_location"]["activity"]
    audio = ctx["technical_setup"]["audio_output"]
    control = ctx["listening_control"]
    affect = state["current_affect"]
    phys = state["physiological_state"]
    functions = p["music_identity"]["listening_functions"]

    # --- probability of listening now ---------------------------------------
    suitability, default_fn = ACTIVITY_LISTENING[activity]
    if activity == "working":
        suitability = p["work_and_occupation"]["schedule"]["can_listen_while_working"] or 0.0
    if audio == "none":
        suitability *= 0.2
    daily = p["routine_and_behavior"]["baseline_listening"]["baseline_daily_listening_probability"]
    listen = clamp(suitability * (0.4 + 0.6 * daily) * (1 - 0.4 * state["music_satiation"]) * (0.6 + 0.4 * control["control_over_music"]))

    # --- what the music is for -----------------------------------------------
    weights = dict(ACTIVITY_FUNCTIONS.get(activity, {default_fn: 2}))
    if affect["valence"] < -0.3:
        weights["emotion_processing"] = weights.get("emotion_processing", 0) + 2
    if phys["stress"] > 0.6:
        weights["relaxation"] = weights.get("relaxation", 0) + 1.5
    scores = {fn: w * (0.2 + functions[fn]) for fn, w in weights.items() if fn != "exercise" or activity == "exercising"}
    primary = max(scores, key=scores.get)

    # --- regulation and target affect -----------------------------------------
    iso = p["emotional_profile"]["regulation"]["iso_principle_adherence"]
    if affect["valence"] < -0.25:
        strategy = "iso_then_shift" if iso >= 0.5 else "shift_toward_desired"
        target = {"valence": r2(clamp(affect["valence"] + 0.5, -1, 1)), "arousal": r2(affect["arousal"] * 0.5)}
    elif phys["stress"] > 0.65 and affect["arousal"] > 0.2:
        strategy = "downregulate"
        target = {"valence": affect["valence"], "arousal": r2(clamp(affect["arousal"] - 0.5, -1, 1))}
    elif phys["energy"] < 0.35 and activity in ("working", "studying", "exercising", "household_chores"):
        strategy = "energize"
        target = {"valence": r2(clamp(affect["valence"] + 0.2, -1, 1)), "arousal": r2(clamp(affect["arousal"] + 0.5, -1, 1))}
    else:
        strategy = "maintain"
        target = {"valence": affect["valence"], "arousal": affect["arousal"]}

    attention = control["available_attention"]
    mode = "foreground" if attention >= 0.6 and control["control_over_music"] >= 0.6 else "partial" if attention >= 0.3 else "background"

    initiation = p["routine_and_behavior"]["listening_initiation"]
    style = p["platform_and_devices"]["platform_behavior"]["playlist_style"]
    source = weighted(rng, {
        "own_playlists": 1 + 2 * (style == "curator") + initiation["active_selection_probability"],
        "search": 0.5 + initiation["active_selection_probability"],
        "album": 0.2 + 2 * (style == "album_based"),
        "recommendations": 0.5 + 2 * (style == "algorithmic") + p["music_identity"]["sensory_and_discovery"]["discovery"]["recommendation_trust"],
        "radio_autoplay": 0.3 + initiation["autoplay_acceptance"],
        "shared_by_friend": 1.0 if activity == "socializing" else 0.1,
    })

    p["derived_listening_intent"] = {
        "listen_probability": r2(listen),
        "primary_function": primary,
        "regulation_strategy": strategy,
        "target_affect": target,
        "attention_mode": mode,
        "selection_source": source,
    }
