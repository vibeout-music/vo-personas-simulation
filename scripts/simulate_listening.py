#!/usr/bin/env python3
"""Simulate one listening moment for every persona and return the song each one plays.

Run it once, or many times a day (by hand or from cron): every run is a new
moment in each persona's life. The moment (context, latent state, intent) is
recomputed for the instant, songs are chosen from the local catalogue for the
reasons that drive that persona, and what they heard is remembered for the
next runs.

Before simulating, the catalogue grows with a small Spotify request budget
(--harvest-requests), unless --offline is given.

Usage:
    python3 scripts/simulate_listening.py                                   # now, 1 song each
    python3 scripts/simulate_listening.py --at 2026-10-01T07:30:00Z --listens 3
    python3 scripts/simulate_listening.py --offline --respect-listen-probability
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vo_personas_simulation.catalog.harvest import harvest  # noqa: E402
from vo_personas_simulation.catalog.spotify import SpotifyClient, SpotifyError, load_credentials  # noqa: E402
from vo_personas_simulation.catalog.store import CatalogStore  # noqa: E402
from vo_personas_simulation.listening.choice import CatalogIndex  # noqa: E402
from vo_personas_simulation.listening.history import ListeningHistory  # noqa: E402
from vo_personas_simulation.listening.session import simulate_persona  # noqa: E402


def parse_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).replace(microsecond=0)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--personas", type=Path, default=ROOT / "data/fixtures/personas_fixture.jsonl")
    parser.add_argument("--at", help="simulated instant in UTC, e.g. 2026-10-01T07:30:00Z (default: now)")
    parser.add_argument("--listens", type=int, default=1, help="songs in a row per persona (default: 1)")
    parser.add_argument("--respect-listen-probability", action="store_true",
                        help="let personas skip music when the moment does not suit it")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--harvest-requests", type=int, default=150, help="Spotify request budget to grow the catalogue first")
    parser.add_argument("--offline", action="store_true", help="do not call Spotify; use the catalogue as it is")
    parser.add_argument("--rate", type=float, default=2.0, help="maximum Spotify requests per second")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog/music.sqlite")
    parser.add_argument("--history", type=Path, default=ROOT / "data/simulation/listening.sqlite")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/generated/listens")
    args = parser.parse_args(argv)

    at = parse_at(args.at)
    run_id = f"{at:%Y%m%dT%H%M%SZ}-s{args.seed}"
    store = CatalogStore(args.catalog)
    history = ListeningHistory(args.history)
    try:
        if history.run_exists(run_id):
            print(f"Run {run_id} already exists in {args.history}: choose another --at or --seed.", file=sys.stderr)
            return 1

        requests = 0
        if not args.offline and args.harvest_requests > 0:
            try:
                client = SpotifyClient(*load_credentials(ROOT / ".env"), budget=args.harvest_requests,
                                       requests_per_second=args.rate)
                summary = harvest(client, store, f"harvest-{run_id}")
                requests = summary["requests"]
                print(f"Catalogue: +{summary['new_tracks']} tracks ({summary['total_tracks']} total, {requests} requests)")
            except SpotifyError as exc:
                if store.track_count() == 0:
                    print(f"Spotify error and the catalogue is empty: {exc}", file=sys.stderr)
                    return 1
                print(f"Spotify error, continuing with the current catalogue: {exc}", file=sys.stderr)

        if store.track_count() == 0:
            print("The music catalogue is empty: run without --offline (with Spotify credentials in .env) "
                  "or run scripts/harvest_catalog.py first.", file=sys.stderr)
            return 1
        catalog = CatalogIndex(store.load_tracks())
        personas = [json.loads(line) for line in args.personas.open(encoding="utf-8") if line.strip()]
        args.out_dir.mkdir(parents=True, exist_ok=True)
        out = args.out_dir / f"{run_id}.jsonl"
        listened = 0
        with out.open("w", encoding="utf-8") as fh:
            for persona in personas:
                line = simulate_persona(persona, at, run_id=run_id, seed=args.seed, catalog=catalog, history=history,
                                        listens=args.listens, respect_listen_probability=args.respect_listen_probability)
                listened += line["listened"]
                fh.write(json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n")
        history.record_run(run_id, at, args.seed, len(personas), args.listens, len(catalog.tracks), requests,
                           datetime.now(timezone.utc))
        print(f"{listened}/{len(personas)} personas listened at {at:%Y-%m-%d %H:%M} UTC "
              f"({len(catalog.tracks)} tracks in the catalogue) -> {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
        return 0
    finally:
        history.close()
        store.close()


if __name__ == "__main__":
    sys.exit(main())
