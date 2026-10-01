#!/usr/bin/env python3
"""Grow the local music catalogue from Spotify, or probe what your Spotify app can use.

Credentials are read from SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET in the
environment or in a .env file at the repository root (never committed).

Usage:
    python3 scripts/harvest_catalog.py --probe          # 3-4 requests: what does my app get?
    python3 scripts/harvest_catalog.py --requests 150   # add tracks, continuing from the last run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vo_personas_simulation.catalog.harvest import harvest, probe  # noqa: E402
from vo_personas_simulation.catalog.spotify import SpotifyClient, SpotifyError, load_credentials  # noqa: E402
from vo_personas_simulation.catalog.store import CatalogStore  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--probe", action="store_true", help="only check what the Spotify app can access")
    parser.add_argument("--requests", type=int, default=150, help="request budget for this run (default: 150)")
    parser.add_argument("--rate", type=float, default=2.0, help="maximum requests per second (default: 2)")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog/music.sqlite")
    args = parser.parse_args(argv)

    store = CatalogStore(args.catalog)
    try:
        client = SpotifyClient(*load_credentials(ROOT / ".env"), budget=6 if args.probe else args.requests,
                               requests_per_second=args.rate)
        if args.probe:
            print(json.dumps(probe(client, store), indent=2))
            return 0
        run_id = datetime.now(timezone.utc).strftime("harvest-%Y%m%dT%H%M%SZ")
        summary = harvest(client, store, run_id)
        print(f"{summary['requests']} requests, {summary['new_tracks']} new tracks, "
              f"{summary['total_tracks']} tracks in {args.catalog}")
        return 0
    except SpotifyError as exc:
        print(f"Spotify error: {exc}", file=sys.stderr)
        return 1
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
