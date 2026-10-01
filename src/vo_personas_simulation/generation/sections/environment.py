"""environmental_sensitivities and platform_and_devices."""

from __future__ import annotations

from ..draft import Draft
from ..sampling import clamp, near, r2, unit, weighted
from ..tables import COUNTRIES
from .emotional import bias

CONTEXT_KEYS = ["mood", "arousal", "activity", "attention", "stress", "fatigue", "loneliness",
                "social_company", "time_of_day", "recent_life_events", "weather", "daylight"]


def build_environment(d: Draft) -> None:
    rng, f = d.rng, d.facts
    n = d.get("psychology.big_five.neuroticism")
    sens = {k: unit(rng, 0.45, 3) for k in CONTEXT_KEYS}
    sens["mood"] = unit(rng, 0.4 + 0.3 * n, 4)
    sens["stress"] = unit(rng, 0.35 + 0.35 * n, 4)
    sens["recent_life_events"] = unit(rng, 0.35 + 0.35 * n, 4)
    weather = sens["weather"]
    privacy = d.get("life_context.living_situation.privacy")
    d.persona["environmental_sensitivities"] = {
        "contextual_sensitivities": {
            "seasonal_sensitivity": near(rng, 0.2 + 0.6 * weather, 0.12),
            "weekend_effect": unit(rng, 0.5 if f["working"] or f["enrolled"] else 0.15, 5),
            "daily_event_sensitivity": near(rng, 0.2 + 0.6 * n, 0.12),
            "special_dates_effect": unit(rng, 0.45, 3),
        },
        "weather_and_time": {
            "weather_mood_impact": {
                # Scaled by how sensitive the person is to weather at all.
                "rainy_day_reaction": r2(weather * rng.uniform(-1, 0.4)),
                "sunny_day_reaction": r2(weather * rng.uniform(-0.2, 1)),
                "overcast_reaction": r2(weather * rng.uniform(-0.8, 0.2)),
            }
        },
        "listening_spaces": {
            "preferred_listening_spaces": {
                "headphones_anc": unit(rng, 0.5 + 0.2 * (privacy < 0.4), 4),
                "car_speakers": unit(rng, 0.6, 3) if f["has_car"] else 0.0,
                "home_speakers": unit(rng, 0.2 + 0.5 * privacy, 4),
            }
        },
        "context_sensitivity": sens,
    }


def build_platform(d: Draft) -> None:
    rng, f = d.rng, d.facts
    b = lambda k: bias(d, k)  # noqa: E731
    economic = d.get("stable_profile.economic_situation")
    age = f["age"]
    arrangement = f["arrangement"]

    paying = rng.random() < clamp(COUNTRIES[f["country"]]["premium"] * (0.5 + economic) + 0.15 * (d.get("music_identity.importance_and_sophistication.identity_centrality") - 0.5))
    if not paying:
        tier = "free"
    else:
        options = {"premium": 3}
        if f["enrolled"] and age >= 18:
            options["student"] = 3
        if arrangement in ("with_parents", "with_partner_and_children", "single_parent", "with_family"):
            options["family"] = 3 if age < 18 else 2
        if arrangement in ("with_partner", "with_partner_and_children"):
            options["duo"] = 1.5
        if age < 18:
            options.pop("premium")  # minors pay through a parent's family plan
        tier = weighted(rng, options)

    devices = ["phone"]
    if age >= 16 or economic > 0.5 or rng.random() < 0.4:
        devices.append("laptop")
    extras = {"desktop": 0.2 + 0.2 * (f["occupation"] in ("software_engineer", "designer")), "tablet": 0.15 + 0.25 * economic,
              "smart_speaker": 0.1 + 0.4 * economic, "tv": 0.35 + 0.3 * economic, "console": 0.35 if age < 35 else 0.1,
              "wearable": 0.1 + 0.3 * economic + 0.2 * f["exerciser"]}
    devices += [dev for dev, p in extras.items() if rng.random() < clamp(p)]
    if f["has_car"]:
        devices.append("car_audio")

    playlist_style = weighted(rng, {"curator": 0.5 + 2 * max(0, b("active")), "algorithmic": 1 + 2 * max(0, b("autoplay")),
                                    "album_based": 0.3 + d.get("music_identity.taste_profile.album_listener_vs_singles"), "mixed": 1.5})
    impulsivity = d.get("psychology.personality_traits.impulsivity")
    d.persona["platform_and_devices"] = {
        "tier": tier,
        "devices": devices,
        "platform_behavior": {
            "playlist_style": playlist_style,
            "social_listening": unit(rng, 0.3 + 0.2 * d.get("psychology.big_five.extraversion") + b("social"), 4),
            "choice_consistency": near(rng, 0.75 - 0.4 * impulsivity, 0.1),
            "behavioural_noise": near(rng, 0.1 + 0.2 * impulsivity, 0.05),
        },
    }
