"""Grow the local catalogue from Spotify search, a budget of requests at a time.

The catalogue is split into cursors: one per (genre, search term, decade,
market). Each run spends its request budget on the cursors that have
contributed least so far and continues from the offset where the previous run
stopped, so every run adds new tracks and the catalogue grows evenly across
genres, eras and countries.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..generation.tables import COUNTRIES, GENRE_ORIGIN, SPOTIFY_QUERIES, genre_birth
from .spotify import BudgetExhausted, SpotifyError
from .store import CatalogStore

MAX_OFFSET = 1000       # Spotify search does not page beyond offset + limit = 1000
FIRST_DECADE = 1950


def build_cursors(current_year: int) -> list[dict]:
    cursors = []
    last_decade = current_year // 10 * 10
    for genre, terms in SPOTIFY_QUERIES.items():
        markets = sorted({c for c, v in COUNTRIES.items() if genre in v["genres"]} | (GENRE_ORIGIN[genre][1].keys() & COUNTRIES.keys()))
        start = max(FIRST_DECADE, genre_birth(genre) // 10 * 10)
        for term in terms:
            for decade in range(start, last_decade + 1, 10):
                for market in markets or [None]:
                    cursors.append({"cursor_id": f"{genre}|{term}|{decade}|{market or '-'}", "genre": genre,
                                    "term": term, "decade": decade, "market": market})
    return cursors


def query_for(term: str, decade: int, genre_filter: bool) -> str:
    years = f"year:{decade}-{decade + 9}"
    return f'genre:"{term}" {years}' if genre_filter else f"{term} {years}"


def probe(client, store: CatalogStore) -> dict:
    """Find out what this app can use: page size, genre filter, and which fields come back."""
    result = {}
    response = None
    for limit in (50, 20, 10):
        try:
            response = client.search_tracks(query_for("rock", 2010, True), market="US", limit=limit, offset=0)
            result["max_limit"] = limit
            break
        except BudgetExhausted:
            raise
        except SpotifyError as exc:
            if "400" not in str(exc):
                raise
    if response is None:
        raise SpotifyError("search did not accept any page size (50, 20 or 10)")
    items = [i for i in response["tracks"]["items"] if i]
    result["genre_filter"] = bool(items)
    if not items:  # genre: filter unsupported for this app -> plain keyword search
        response = client.search_tracks(query_for("rock", 2010, False), market="US", limit=result["max_limit"], offset=0)
        items = [i for i in response["tracks"]["items"] if i]
    result["popularity"] = any(i.get("popularity") is not None for i in items)
    result["release_date"] = any((i.get("album") or {}).get("release_date") for i in items)
    result["available_markets"] = any("available_markets" in i for i in items)
    result["artist_genres"] = False
    artist_id = next((a["id"] for i in items for a in i.get("artists", []) if a.get("id")), None)
    if artist_id:
        try:
            result["artist_genres"] = bool(client.artist(artist_id).get("genres"))
        except SpotifyError:
            pass
    result["probed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    store.set_setting("probe", result)
    return result


def harvest(client, store: CatalogStore, run_id: str, now: datetime | None = None) -> dict:
    """Spend the client's request budget adding tracks. Returns a summary of the run."""
    now = now or datetime.now(timezone.utc)
    settings = store.get_setting("probe") or probe(client, store)
    limit, genre_filter = settings["max_limit"], settings["genre_filter"]
    store.ensure_cursors(build_cursors(now.year))
    new_tracks = 0
    while True:
        cursor = store.next_cursor()
        if cursor is None:
            break  # everything reachable has been harvested
        offset = cursor["next_offset"]
        try:
            response = client.search_tracks(query_for(cursor["term"], cursor["decade"], genre_filter),
                                            market=cursor["market"], limit=limit, offset=offset)
        except BudgetExhausted:
            break
        except SpotifyError:
            store.advance_cursor(cursor["cursor_id"], step=0, found=0, exhausted=True)  # a query Spotify rejects
            continue
        page = response.get("tracks") or {}
        items = [i for i in page.get("items") or [] if i and i.get("id")]
        found = sum(store.add_track(item, cursor["genre"], cursor["market"]) for item in items)
        new_tracks += found
        exhausted = len(items) < limit or not page.get("next") or offset + 2 * limit > MAX_OFFSET
        store.advance_cursor(cursor["cursor_id"], step=limit, found=found, exhausted=exhausted)
        store.db.commit()
    store.record_run(run_id, client.requests_made, new_tracks)
    return {"run_id": run_id, "requests": client.requests_made, "new_tracks": new_tracks, "total_tracks": store.track_count()}
