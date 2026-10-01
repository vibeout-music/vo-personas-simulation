"""Population-level checks: every persona is coherent, generation is reproducible, distributions are plausible."""

import json
import statistics
import sys
import unittest
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vo_personas_simulation.generation.population import generate_persona, generate_population  # noqa: E402
from vo_personas_simulation.generation.sections.state import life_event_pressure  # noqa: E402
from vo_personas_simulation.generation.tables import genre_arrival  # noqa: E402

REFERENCE = datetime(2026, 9, 1, tzinfo=timezone.utc)
TODAY = date(2026, 9, 1)
SIZE = 2000


class PopulationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.personas = list(generate_population(SIZE, 42, REFERENCE))  # raises on any incoherent persona

    def test_reproducible(self):
        for i in (0, 17, SIZE - 1):
            self.assertEqual(json.dumps(generate_persona(i, 42, REFERENCE)), json.dumps(self.personas[i]))

    def test_different_seed_gives_different_population(self):
        self.assertNotEqual(generate_persona(0, 7, REFERENCE), self.personas[0])

    def test_all_life_stages_present(self):
        stages = Counter(p["stable_profile"]["demographics"]["life_stage"] for p in self.personas)
        self.assertEqual(set(stages), {"teenager", "young_adult", "early_career", "established_adult", "midlife", "senior"})
        self.assertGreater(stages["teenager"] / SIZE, 0.02)

    def test_archetypes_are_mixed(self):
        mixed = sum(len(p["metadata"]["archetype_mix"]) > 1 for p in self.personas)
        self.assertGreater(mixed / SIZE, 0.4)

    def test_taste_is_varied(self):
        favourites = Counter(next(iter(p["music_identity"]["genres_and_styles"]["genre_affinities"])) for p in self.personas)
        self.assertGreater(len(favourites), 30)
        self.assertLess(favourites.most_common(1)[0][1] / SIZE, 0.15)

    def test_correlated_traits_follow_each_other(self):
        n = [p["psychology"]["big_five"]["neuroticism"] for p in self.personas]
        esteem = [p["psychology"]["personality_traits"]["self_esteem"] for p in self.personas]
        dominance = [p["emotional_profile"]["baseline"]["dominance"] for p in self.personas]
        self.assertLess(statistics.correlation(esteem, n), -0.4)
        self.assertGreater(statistics.correlation(dominance, esteem), 0.25)
        # ...but not deterministically: some anxious people still have high self-esteem.
        self.assertTrue(any(ni > 0.7 and ei > 0.6 for ni, ei in zip(n, esteem)))

    def test_no_absolute_preferences(self):
        for p in self.personas:
            for feature in p["music_identity"]["audio_features"]["audio_feature_preferences"].values():
                self.assertTrue(0.02 <= feature["ideal"] <= 0.98 and 0.02 <= feature["tolerance"] <= 0.98)

    def test_age_shapes_taste_without_fixing_it(self):
        def post_youth(p):
            country, end = p["stable_profile"]["residency"]["country"], p["stable_profile"]["formative_music_years"][1]
            return [v for g, v in p["music_identity"]["genres_and_styles"]["genre_affinities"].items() if genre_arrival(g, country) > end]
        older = [p for p in self.personas if p["stable_profile"]["demographics"]["age"] >= 55]
        younger = [p for p in self.personas if p["stable_profile"]["demographics"]["age"] <= 30]
        older_mean = statistics.mean(v for p in older for v in post_youth(p))
        younger_mean = statistics.mean(v for p in younger for v in post_youth(p))
        self.assertLess(older_mean, younger_mean)
        fans = sum(any(v >= 0.5 for v in post_youth(p)) for p in older)
        self.assertGreater(fans / len(older), 0.3)  # many older people still love newer music

    def test_contexts_cover_the_day(self):
        hours = {int(p["current_context"]["temporal"]["local_time"][11:13]) for p in self.personas}
        self.assertEqual(hours, set(range(24)))


class LifeEventTest(unittest.TestCase):
    @staticmethod
    def persona_with(days_ago, recovery_rate=0.5):
        started = (TODAY - timedelta(days=days_ago)).isoformat()
        return {
            "emotional_profile": {"dynamics": {"recovery_rate": recovery_rate}},
            "life_context": {"life_events": {"active_life_events": [
                {"event_type": "bereavement", "started_on": started, "valence_impact": -0.8, "intensity": 0.7}]}},
        }

    def test_recent_loss_weighs_more_than_an_old_one(self):
        recent, _, lonely_recent = life_event_pressure(self.persona_with(4), TODAY)
        old, _, lonely_old = life_event_pressure(self.persona_with(110), TODAY)
        self.assertLess(recent, old)
        self.assertTrue(lonely_recent)
        self.assertFalse(lonely_old)

    def test_resilient_people_are_less_shaken(self):
        fragile, _, _ = life_event_pressure(self.persona_with(4, recovery_rate=0.1), TODAY)
        resilient, _, _ = life_event_pressure(self.persona_with(4, recovery_rate=0.9), TODAY)
        self.assertLess(fragile, resilient)


if __name__ == "__main__":
    unittest.main()
