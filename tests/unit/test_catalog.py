"""Catalogue: estimated features, harvesting with a fake Spotify, and the real client's retry logic."""

import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from fakes import FakeSpotify  # noqa: E402
from vo_personas_simulation.catalog.features import emotion_profile, estimate_features, estimate_languages  # noqa: E402
from vo_personas_simulation.catalog.harvest import harvest  # noqa: E402
from vo_personas_simulation.catalog.spotify import SpotifyClient  # noqa: E402
from vo_personas_simulation.catalog.store import CatalogStore  # noqa: E402


class FeaturesTest(unittest.TestCase):
    def test_same_track_same_features(self):
        a = estimate_features("spotify:track:abc", ["techno"], 2015, 60)
        self.assertEqual(a, estimate_features("spotify:track:abc", ["techno"], 2015, 60))

    def test_genres_shape_the_sound(self):
        techno = [estimate_features(f"spotify:track:t{i}", ["techno"], 2015, 50) for i in range(50)]
        classical = [estimate_features(f"spotify:track:c{i}", ["classical"], 2015, 50) for i in range(50)]
        mean = lambda xs, k: sum(x[k] for x in xs) / len(xs)  # noqa: E731
        self.assertGreater(mean(techno, "energy"), mean(classical, "energy") + 0.4)
        self.assertGreater(mean(classical, "acousticness"), mean(techno, "acousticness") + 0.5)

    def test_features_stay_in_range(self):
        for i in range(200):
            f = estimate_features(f"spotify:track:{i}", ["metal", "punk"], 1975, 99)
            self.assertTrue(all(0.02 <= f[k] <= 0.98 for k in ("energy", "valence", "danceability", "acousticness", "instrumentalness")))
            e = emotion_profile(f)
            self.assertTrue(-1 <= e["valence"] <= 1 and -1 <= e["arousal"] <= 1)

    def test_languages(self):
        self.assertEqual(estimate_languages(["kpop"], "US", 0.1), ["ko"])
        self.assertEqual(estimate_languages(["classical"], None, 0.9), ["instrumental"])
        self.assertEqual(estimate_languages(["italian_pop"], "IT", 0.1), ["it"])


class HarvestTest(unittest.TestCase):
    def setUp(self):
        self.store = CatalogStore(":memory:")

    def tearDown(self):
        self.store.close()

    def test_budget_is_respected(self):
        client = FakeSpotify(budget=25)
        summary = harvest(client, self.store, "run-1")
        self.assertEqual(client.requests_made, 25)
        self.assertEqual(summary["requests"], 25)
        self.assertGreater(summary["new_tracks"], 0)

    def test_each_run_continues_where_the_last_stopped(self):
        first = harvest(FakeSpotify(budget=30), self.store, "run-1")
        client = FakeSpotify(budget=30)
        second = harvest(client, self.store, "run-2")
        self.assertGreater(second["new_tracks"], 0)
        self.assertEqual(second["total_tracks"], first["total_tracks"] + second["new_tracks"])
        # No (query, offset) page is fetched twice.
        offsets = self.store.db.execute("SELECT SUM(next_offset) FROM harvest_cursors").fetchone()[0]
        self.assertGreater(offsets, 0)

    def test_a_track_found_twice_is_stored_once_with_both_genres(self):
        harvest(FakeSpotify(budget=400), self.store, "run-1")
        multi = self.store.db.execute(
            "SELECT track_id, COUNT(*) AS n FROM track_genres GROUP BY track_id HAVING n > 1").fetchall()
        self.assertTrue(multi)
        ids = [r["track_id"] for r in self.store.db.execute("SELECT track_id FROM tracks")]
        self.assertEqual(len(ids), len(set(ids)))

    def test_rejected_queries_are_skipped(self):
        harvest(FakeSpotify(budget=60, reject_terms={"afrobeats"}), self.store, "run-1")
        rows = self.store.db.execute("SELECT exhausted, tracks_found FROM harvest_cursors WHERE genre = 'afrobeats' AND requests > 0").fetchall()
        self.assertTrue(rows and all(r["exhausted"] and r["tracks_found"] == 0 for r in rows))


class SpotifyClientTest(unittest.TestCase):
    def test_retries_after_rate_limit_and_counts_requests(self):
        client = SpotifyClient("id", "secret", budget=10, requests_per_second=1000)
        client._token, client._token_expires = "token", 1e12
        limited = urllib.error.HTTPError("url", 429, "Too Many Requests", {"Retry-After": "0"}, io.BytesIO(b""))
        ok = mock.MagicMock()
        ok.__enter__.return_value = io.BytesIO(json.dumps({"tracks": {"items": []}}).encode())
        with mock.patch("urllib.request.urlopen", side_effect=[limited, ok]), mock.patch("time.sleep"):
            result = client.search_tracks("genre:\"rock\"", market="US", limit=10, offset=0)
        self.assertEqual(result, {"tracks": {"items": []}})
        self.assertEqual(client.requests_made, 2)

    def test_never_exceeds_budget(self):
        from vo_personas_simulation.catalog.spotify import BudgetExhausted
        client = SpotifyClient("id", "secret", budget=0)
        with self.assertRaises(BudgetExhausted):
            client.search_tracks("x", market=None, limit=10, offset=0)


if __name__ == "__main__":
    unittest.main()
