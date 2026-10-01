"""A deterministic stand-in for the Spotify API, so tests never touch the network."""

import hashlib
import re

from vo_personas_simulation.catalog.spotify import BudgetExhausted, SpotifyError

RESULTS_PER_QUERY = 120


def _h(*parts) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:22]


class FakeSpotify:
    """Answers track searches with synthetic but stable results.

    Every tenth result is shared between related genre searches of the same
    decade, like a real track that several genre searches find.
    """

    def __init__(self, budget: int, reject_terms=()):
        self.budget = budget
        self.requests_made = 0
        self.reject_terms = set(reject_terms)
        self.queries = []

    def _count(self):
        if self.requests_made >= self.budget:
            raise BudgetExhausted("budget used")
        self.requests_made += 1

    def search_tracks(self, query, *, market, limit, offset):
        self._count()
        self.queries.append((query, market, limit, offset))
        term = re.search(r'genre:"([^"]+)"', query).group(1)
        if term in self.reject_terms:
            raise SpotifyError("GET /search failed with 400: bad query")
        decade = int(re.search(r"year:(\d{4})", query).group(1))
        items = []
        for i in range(offset, min(offset + limit, RESULTS_PER_QUERY)):
            shared = i % 10 == 0
            # Shared between related searches only (e.g. "latin pop" and "italian pop" share "pop").
            track_id = _h("shared", decade, i, term.split()[-1]) if shared else _h(term, decade, market, i)
            items.append({
                "id": track_id,
                "name": f"{term.title()} song {i}",
                "duration_ms": 150_000 + (i % 9) * 15_000,
                "explicit": i % 7 == 0,
                "popularity": (i * 37) % 100,
                "album": {"name": f"{term.title()} album {i // 12}", "release_date": f"{decade + i % 10}-05-01"},
                "artists": [{"id": _h("artist", term, i % 8), "name": f"{term.title()} Artist {i % 8}"}],
                "external_urls": {"spotify": f"https://open.spotify.com/track/{track_id}"},
            })
        has_next = offset + limit < RESULTS_PER_QUERY
        return {"tracks": {"items": items, "next": "more" if has_next else None, "total": RESULTS_PER_QUERY}}

    def artist(self, artist_id):
        self._count()
        return {"id": artist_id, "genres": []}
