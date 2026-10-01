"""Persistent listening history: what each persona heard, and what they remember of it.

Tables follow the entity contracts (ObservableEvent, PersonTrackState) in
spirit, kept compact for a local SQLite store. Memory is sparse: a row exists
only after a persona has actually met a track or artist.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY, simulated_at TEXT NOT NULL, seed INTEGER NOT NULL, personas INTEGER NOT NULL,
    listens INTEGER NOT NULL, catalog_tracks INTEGER NOT NULL, harvest_requests INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS listening_events (
    event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, persona_id TEXT NOT NULL, occurred_at TEXT NOT NULL,
    local_time TEXT NOT NULL, position INTEGER NOT NULL, track_id TEXT NOT NULL, artist_ids TEXT NOT NULL,
    outcome TEXT NOT NULL, listened_ms INTEGER NOT NULL, liked INTEGER NOT NULL,
    context TEXT NOT NULL, state TEXT NOT NULL, reasons TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_persona ON listening_events (persona_id, occurred_at);
CREATE TABLE IF NOT EXISTS person_track_state (
    persona_id TEXT NOT NULL, track_id TEXT NOT NULL,
    familiarity REAL NOT NULL, learned_affinity REAL NOT NULL, satiation REAL NOT NULL,
    exposure_count INTEGER NOT NULL, play_count INTEGER NOT NULL, skip_count INTEGER NOT NULL,
    last_played_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    PRIMARY KEY (persona_id, track_id)
);
CREATE TABLE IF NOT EXISTS person_artist_state (
    persona_id TEXT NOT NULL, artist_id TEXT NOT NULL, familiarity REAL NOT NULL, play_count INTEGER NOT NULL,
    last_played_at TEXT NOT NULL,
    PRIMARY KEY (persona_id, artist_id)
);
"""


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def effective_satiation(state: dict, now: datetime, habituation: float) -> float:
    """Tiredness of a track right now: it fades with time, slower for people who habituate strongly."""
    hours = max(0.0, (now - parse_ts(state["last_played_at"])).total_seconds() / 3600)
    half_life = 12 + 60 * habituation
    return state["satiation"] * 0.5 ** (hours / half_life)


class ListeningHistory:
    def __init__(self, path: Path | str):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.commit()
        self.db.close()

    def run_exists(self, run_id: str) -> bool:
        return self.db.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone() is not None

    def record_run(self, run_id: str, simulated_at: datetime, seed: int, personas: int, listens: int,
                   catalog_tracks: int, harvest_requests: int, created_at: datetime) -> None:
        self.db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (run_id, iso(simulated_at), seed, personas, listens, catalog_tracks, harvest_requests, iso(created_at)))
        self.db.commit()

    def load_memory(self, persona_id: str) -> dict:
        tracks = {r["track_id"]: dict(r) for r in self.db.execute(
            "SELECT * FROM person_track_state WHERE persona_id = ?", (persona_id,))}
        artists = {r["artist_id"]: dict(r) for r in self.db.execute(
            "SELECT * FROM person_artist_state WHERE persona_id = ?", (persona_id,))}
        return {"tracks": tracks, "artists": artists}

    def record_listen(self, *, event_id: str, run_id: str, persona_id: str, when: datetime, local_time: str,
                      position: int, track: dict, outcome: str, listened_ms: int, liked: bool,
                      context: dict, state: dict, reasons: list, memory: dict) -> None:
        """Store the event and update the persona's memory of the track and its artists (in `memory` too)."""
        now = iso(when)
        self.db.execute(
            "INSERT INTO listening_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, run_id, persona_id, now, local_time, position, track["track_id"],
             json.dumps([a["artist_id"] for a in track["artists"]]), outcome, listened_ms, int(liked),
             json.dumps(context), json.dumps(state), json.dumps(reasons)))
        row = memory["tracks"][track["track_id"]]
        self.db.execute(
            "INSERT OR REPLACE INTO person_track_state VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (persona_id, track["track_id"], row["familiarity"], row["learned_affinity"], row["satiation"],
             row["exposure_count"], row["play_count"], row["skip_count"], row["last_played_at"], now))
        for artist in track["artists"]:
            a = memory["artists"][artist["artist_id"]]
            self.db.execute("INSERT OR REPLACE INTO person_artist_state VALUES (?, ?, ?, ?, ?)",
                            (persona_id, artist["artist_id"], a["familiarity"], a["play_count"], a["last_played_at"]))


def remember(memory: dict, track: dict, *, outcome: str, liked: bool, when: datetime, habituation: float) -> None:
    """Update the in-memory track and artist state after a listen."""
    now = iso(when)
    prev = memory["tracks"].get(track["track_id"])
    completed = outcome == "completed"
    satiation = effective_satiation(prev, when, habituation) if prev else 0.0
    familiarity = prev["familiarity"] if prev else 0.0
    affinity = prev["learned_affinity"] if prev else 0.0
    signal = 1.0 if liked else 0.5 if completed else -0.6
    memory["tracks"][track["track_id"]] = {
        "familiarity": round(familiarity + (1 - familiarity) * (0.25 if completed else 0.08), 4),
        "learned_affinity": round(0.7 * affinity + 0.3 * signal, 4),
        "satiation": round(min(1.5, satiation + (0.35 if completed else 0.1)), 4),
        "exposure_count": (prev["exposure_count"] if prev else 0) + 1,
        "play_count": (prev["play_count"] if prev else 0) + int(completed),
        "skip_count": (prev["skip_count"] if prev else 0) + int(not completed),
        "last_played_at": now,
    }
    for artist in track["artists"]:
        a = memory["artists"].get(artist["artist_id"], {"familiarity": 0.0, "play_count": 0})
        memory["artists"][artist["artist_id"]] = {
            "familiarity": round(a["familiarity"] + (1 - a["familiarity"]) * (0.15 if completed else 0.05), 4),
            "play_count": a["play_count"] + int(completed),
            "last_played_at": now,
        }
