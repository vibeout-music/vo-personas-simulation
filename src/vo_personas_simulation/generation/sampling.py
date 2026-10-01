"""Deterministic sampling helpers."""

from __future__ import annotations

import hashlib
import math
import random


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def r2(x: float) -> float:
    return round(x, 2)


# Traits never sit exactly at 0 or 1: nobody has zero tolerance or perfect security.
TRAIT_MIN, TRAIT_MAX = 0.02, 0.98


def unit(rng: random.Random, mean: float = 0.5, concentration: float = 5.0) -> float:
    """Beta-distributed trait in [0.02, 0.98] with the given mean.

    Low concentration (2-4) for traits that vary freely between people; higher
    (7-10) for traits that should follow the traits they depend on, while still
    leaving room for people who do not.
    """
    mean = clamp(mean, 0.03, 0.97)
    return r2(clamp(rng.betavariate(mean * concentration, (1 - mean) * concentration), TRAIT_MIN, TRAIT_MAX))


def signed(rng: random.Random, mean: float = 0.0, concentration: float = 5.0) -> float:
    """Beta-distributed value in [-1, 1] with the given mean."""
    return r2(unit(rng, (mean + 1) / 2, concentration) * 2 - 1)


def near(rng: random.Random, value: float, spread: float = 0.1, lo: float = TRAIT_MIN, hi: float = TRAIT_MAX) -> float:
    """A value correlated with ``value``."""
    return r2(clamp(value + rng.gauss(0, spread), lo, hi))


def poisson(rng: random.Random, lam: float) -> int:
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def weighted(rng: random.Random, options: dict):
    keys = [k for k, w in options.items() if w > 0]
    return rng.choices(keys, weights=[options[k] for k in keys])[0]


def derive_seed(*parts) -> int:
    digest = hashlib.sha256(":".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:4], "big") % 1_000_000
