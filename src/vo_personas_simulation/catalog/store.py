"""Local music catalogue that grows with every harvest (SQLite, standard library)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .features import emotion_profile, estimate_features, estimate_languages

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    track_id TEXT PRIMARY KEY,          -- spotify:track:<id>
    spotify_id TEXT NOT NULL,
    title TEXT NOT NULL,
    album TEXT,
    release_year INTEGER,
    duration_ms INTEGER,
    explicit INTEGER,
    popularity INTEGER,                 -- NULL when the API does not return it
    spotify_url TEXT,
    market TEXT,                        -- market where it was found
    languages TEXT NOT NULL,            -- JSON list, estimated
    audio_features TEXT NOT NULL,       -- JSON, estimated
    emotion_profile TEXT NOT NULL,      -- JSON, estimated
    features_source TEXT NOT NULL DEFAULT 'estimated',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS artists (
    artist_id TEXT PRIMARY KEY,         -- spotify:artist:<id>
    name TEXT NOT NULL,
    spotify_genres TEXT                 -- JSON list, NULL if never fetched
);
CREATE TABLE IF NOT EXISTS track_artists (
    track_id TEXT NOT NULL, artist_id TEXT NOT NULL, position INTEGER NOT NULL,
    PRIMARY KEY (track_id, artist_id)
);
CREATE TABLE IF NOT EXISTS track_genres (
    track_id TEXT NOT NULL, genre TEXT NOT NULL,
    PRIMARY KEY (track_id, genre)
);
CREATE INDEX IF NOT EXISTS idx_track_genres_genre ON track_genres (genre);
CREATE TABLE IF NOT EXISTS harvest_cursors (
    cursor_id TEXT PRIMARY KEY,         -- genre|term|decade|market
    genre TEXT NOT NULL, term TEXT NOT NULL, decade INTEGER NOT NULL, market TEXT,
    next_offset INTEGER NOT NULL DEFAULT 0,
    requests INTEGER NOT NULL DEFAULT 0,
    tracks_found INTEGER NOT NULL DEFAULT 0,
    exhausted INTEGER NOT NULL DEFAULT 0,
    last_run TEXT
);
CREATE TABLE IF NOT EXISTS harvest_runs (
    run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, requests INTEGER NOT NULL,
    new_tracks INTEGER NOT NULL, total_tracks INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class CatalogStore:
    def __init__(self, path: Path | str):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.commit()
        self.db.close()

    # --- settings (probe results) ------------------------------------------------

    def get_setting(self, key: str, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def set_setting(self, key: str, value) -> None:
        self.db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
        self.db.commit()

    # --- tracks -----------------------------------------------------------------------

    def add_track(self, item: dict, genre: str, market: str | None) -> bool:
        """Store a Spotify track object found while searching ``genre``. Returns True if it is new."""
        track_id = f"spotify:track:{item['id']}"
        seen = now_iso()
        exists = self.db.execute("SELECT 1 FROM tracks WHERE track_id = ?", (track_id,)).fetchone()
        self.db.execute("INSERT OR IGNORE INTO track_genres (track_id, genre) VALUES (?, ?)", (track_id, genre))
        genres = [r["genre"] for r in self.db.execute("SELECT genre FROM track_genres WHERE track_id = ? ORDER BY genre", (track_id,))]
        release = (item.get("album") or {}).get("release_date") or ""
        year = int(release[:4]) if release[:4].isdigit() else None
        popularity = item.get("popularity")
        features = estimate_features(track_id, genres, year, popularity)
        emotion = emotion_profile(features)
        languages = estimate_languages(genres, market, features["instrumentalness"])
        if exists:
            # Found again through another genre: keep one track, re-estimate with all its genres.
            self.db.execute(
                "UPDATE tracks SET last_seen = ?, audio_features = ?, emotion_profile = ?, languages = ? WHERE track_id = ?",
                (seen, json.dumps(features), json.dumps(emotion), json.dumps(languages), track_id))
            return False
        self.db.execute(
            """INSERT INTO tracks (track_id, spotify_id, title, album, release_year, duration_ms, explicit, popularity,
                                   spotify_url, market, languages, audio_features, emotion_profile, first_seen, last_seen)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (track_id, item["id"], item.get("name", ""), (item.get("album") or {}).get("name"), year,
             item.get("duration_ms"), int(bool(item.get("explicit"))), popularity,
             (item.get("external_urls") or {}).get("spotify"), market, json.dumps(languages),
             json.dumps(features), json.dumps(emotion), seen, seen))
        for pos, artist in enumerate(item.get("artists") or []):
            if not artist.get("id"):
                continue
            artist_id = f"spotify:artist:{artist['id']}"
            self.db.execute("INSERT OR IGNORE INTO artists (artist_id, name) VALUES (?, ?)", (artist_id, artist.get("name", "")))
            self.db.execute("INSERT OR IGNORE INTO track_artists (track_id, artist_id, position) VALUES (?, ?, ?)",
                            (track_id, artist_id, pos))
        return True

    def track_count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]

    def version(self) -> dict:
        row = self.db.execute("SELECT COUNT(*) AS n, MAX(first_seen) AS latest FROM tracks").fetchone()
        return {"tracks": row["n"], "latest_addition": row["latest"]}

    def load_tracks(self) -> list[dict]:
        """The whole catalogue in memory, in a stable order (for deterministic choices)."""
        artists = {}
        for r in self.db.execute(
                "SELECT ta.track_id, a.artist_id, a.name FROM track_artists ta JOIN artists a USING (artist_id) ORDER BY ta.track_id, ta.position"):
            artists.setdefault(r["track_id"], []).append({"artist_id": r["artist_id"], "name": r["name"]})
        genres = {}
        for r in self.db.execute("SELECT track_id, genre FROM track_genres ORDER BY track_id, genre"):
            genres.setdefault(r["track_id"], []).append(r["genre"])
        tracks = []
        for r in self.db.execute("SELECT * FROM tracks ORDER BY track_id"):
            tracks.append({
                "track_id": r["track_id"], "title": r["title"], "album": r["album"], "year": r["release_year"],
                "duration_ms": r["duration_ms"], "explicit": bool(r["explicit"]), "popularity": r["popularity"],
                "spotify_url": r["spotify_url"], "market": r["market"], "languages": json.loads(r["languages"]),
                "audio_features": json.loads(r["audio_features"]), "emotion_profile": json.loads(r["emotion_profile"]),
                "features_source": r["features_source"], "genres": genres.get(r["track_id"], []),
                "artists": artists.get(r["track_id"], []),
            })
        return tracks

    # --- harvest cursors ----------------------------------------------------------------

    def ensure_cursors(self, cursors: list[dict]) -> None:
        self.db.executemany(
            "INSERT OR IGNORE INTO harvest_cursors (cursor_id, genre, term, decade, market) VALUES (:cursor_id, :genre, :term, :decade, :market)",
            cursors)
        self.db.commit()

    def next_cursor(self):
        """The open cursor that has contributed least so far, so the catalogue grows evenly."""
        return self.db.execute(
            "SELECT * FROM harvest_cursors WHERE exhausted = 0 ORDER BY tracks_found, requests, cursor_id LIMIT 1").fetchone()

    def advance_cursor(self, cursor_id: str, *, step: int, found: int, exhausted: bool) -> None:
        self.db.execute(
            """UPDATE harvest_cursors SET next_offset = next_offset + ?, requests = requests + 1,
                      tracks_found = tracks_found + ?, exhausted = ?, last_run = ? WHERE cursor_id = ?""",
            (step, found, int(exhausted), now_iso(), cursor_id))

    def record_run(self, run_id: str, requests: int, new_tracks: int) -> None:
        self.db.execute("INSERT OR REPLACE INTO harvest_runs VALUES (?, ?, ?, ?, ?)",
                        (run_id, now_iso(), requests, new_tracks, self.track_count()))
        self.db.commit()
