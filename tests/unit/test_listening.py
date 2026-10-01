"""Listening: moments at any instant, song choice, and memory across runs."""

import copy
import random
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from fakes import FakeSpotify  # noqa: E402
from vo_personas_simulation.catalog.harvest import harvest  # noqa: E402
from vo_personas_simulation.catalog.store import CatalogStore  # noqa: E402
from vo_personas_simulation.generation.moment import build_moment  # noqa: E402
from vo_personas_simulation.generation.population import generate_persona  # noqa: E402
from vo_personas_simulation.generation.rules import validate  # noqa: E402
from vo_personas_simulation.generation.sampling import derive_seed  # noqa: E402
from vo_personas_simulation.listening.choice import CatalogIndex, choose  # noqa: E402
from vo_personas_simulation.listening.history import ListeningHistory  # noqa: E402
from vo_personas_simulation.listening.session import simulate_persona  # noqa: E402

REFERENCE = datetime(2026, 9, 1, tzinfo=timezone.utc)
MONDAY = datetime(2026, 10, 5, tzinfo=timezone.utc)
_catalog = None


def catalog() -> CatalogIndex:
    global _catalog
    if _catalog is None:
        store = CatalogStore(":memory:")
        harvest(FakeSpotify(budget=500), store, "fixture")
        _catalog = CatalogIndex(store.load_tracks())
        store.close()
    return _catalog


class MomentTest(unittest.TestCase):
    def test_original_instant_reproduces_the_generated_persona(self):
        for i in range(20):
            p = generate_persona(i, 42, REFERENCE)
            when = datetime.fromisoformat(p["current_context"]["timestamp"].replace("Z", "+00:00"))
            self.assertEqual(build_moment(p, when, derive_seed(p["metadata"]["seed"], "moment")), p)

    def test_any_moment_is_coherent(self):
        for i in range(40):
            p = generate_persona(i, 42, REFERENCE)
            for hours in range(0, 24 * 60, 37):  # two months, every hour of the day
                when = MONDAY + timedelta(hours=hours)
                self.assertEqual(validate(build_moment(p, when, i + hours)), [])

    def test_stable_profile_does_not_change(self):
        p = generate_persona(3, 42, REFERENCE)
        m = build_moment(p, MONDAY, 1)
        for section in ("psychology", "music_identity", "work_and_occupation", "life_context"):
            self.assertEqual(m[section], p[section])


class ChoiceTest(unittest.TestCase):
    def persona_doing(self, activity: str, function: str, energy: float) -> dict:
        p = copy.deepcopy(generate_persona(5, 42, REFERENCE))
        p["current_context"]["activity_and_location"]["activity"] = activity
        p["derived_listening_intent"]["primary_function"] = function
        p["derived_listening_intent"]["regulation_strategy"] = "maintain"
        p["mutable_state"]["physiological_state"]["energy"] = energy
        p["environmental_sensitivities"]["context_sensitivity"]["activity"] = 0.9
        return p

    def mean_chosen(self, p, feature, n=40, key=None):
        values = []
        for i in range(n):
            c = choose(p, catalog(), {"tracks": {}, "artists": {}}, random.Random(i), MONDAY)
            values.append(key(c.track) if key else c.track["audio_features"][feature])
        return sum(values) / len(values)

    def test_exercise_music_is_more_energetic_than_relaxing_music(self):
        workout = self.mean_chosen(self.persona_doing("exercising", "exercise", 0.3), "energy")
        unwind = self.mean_chosen(self.persona_doing("relaxing", "relaxation", 0.3), "energy")
        self.assertGreater(workout, unwind + 0.1)

    def test_popularity_bias_pulls_towards_hits(self):
        p = self.persona_doing("relaxing", "background", 0.5)
        hits, obscure = copy.deepcopy(p), copy.deepcopy(p)
        hits["music_identity"]["sensory_and_discovery"]["discovery"]["popularity_bias"] = 0.95
        obscure["music_identity"]["sensory_and_discovery"]["discovery"]["popularity_bias"] = 0.05
        pop = lambda t: t["popularity"]  # noqa: E731
        self.assertGreater(self.mean_chosen(hits, None, key=pop), self.mean_chosen(obscure, None, key=pop) + 10)

    def test_choice_explains_itself(self):
        c = choose(generate_persona(1, 42, REFERENCE), catalog(), {"tracks": {}, "artists": {}}, random.Random(0), MONDAY)
        self.assertTrue(1 <= len(c.reasons) <= 3)
        self.assertTrue(all(r["detail"] and r["factor"] in c.contributions for r in c.reasons))


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.history = ListeningHistory(":memory:")

    def tearDown(self):
        self.history.close()

    def run_at(self, persona, when, run_id, **kw):
        return simulate_persona(persona, when, run_id=run_id, seed=42, catalog=catalog(), history=self.history, **kw)

    def test_different_moments_give_different_songs(self):
        p = generate_persona(0, 42, REFERENCE)
        songs = [self.run_at(p, MONDAY + timedelta(hours=h), f"r{h}")["song_of_the_moment"]["track_id"] for h in (7, 13, 21)]
        self.assertEqual(len(set(songs)), 3)

    def test_same_inputs_same_result(self):
        p = generate_persona(0, 42, REFERENCE)
        a = self.run_at(p, MONDAY, "a")
        other = ListeningHistory(":memory:")
        b = simulate_persona(p, MONDAY, run_id="a", seed=42, catalog=catalog(), history=other)
        other.close()
        self.assertEqual(a, b)

    def test_memory_counts_plays_and_skips(self):
        p = generate_persona(2, 42, REFERENCE)
        line = self.run_at(p, MONDAY, "r1", listens=5)
        memory = self.history.load_memory(p["metadata"]["persona_id"])
        plays = sum(s["play_count"] for s in memory["tracks"].values())
        skips = sum(s["skip_count"] for s in memory["tracks"].values())
        self.assertEqual(plays, sum(x["outcome"] == "completed" for x in line["listens"]))
        self.assertEqual(plays + skips, 5)

    def test_recent_songs_are_less_likely_to_repeat(self):
        p = copy.deepcopy(generate_persona(4, 42, REFERENCE))
        p["routine_and_behavior"]["replay_and_habituation"]["obsessive_replay"] = 0.05
        first = self.run_at(p, MONDAY, "r1", listens=10)
        heard = {x["track_id"] for x in first["listens"] if x["outcome"] == "completed"}
        later = self.run_at(p, MONDAY + timedelta(minutes=45), "r2", listens=10)
        repeats = sum(x["track_id"] in heard for x in later["listens"])
        self.assertLessEqual(repeats, 1)

    def test_personas_can_sit_music_out(self):
        silent = 0
        for i in range(30):
            p = generate_persona(i, 42, REFERENCE)
            line = self.run_at(p, MONDAY.replace(hour=1), f"n{i}", respect_listen_probability=True)
            silent += not line["listened"]
        self.assertGreater(silent, 0)


if __name__ == "__main__":
    unittest.main()
