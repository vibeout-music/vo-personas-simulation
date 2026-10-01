#!/usr/bin/env python3
"""Generate a deterministic population of synthetic personas as JSONL.

One persona per line, following schemas/persona-unified-schema.json. Every
persona is checked against the schema's shape and the coherence rules in
src/vo_personas_simulation/generation/rules.py; generation stops on the first
incoherent persona.

The same --seed and --reference-date always produce the same file.

Usage:
    python3 scripts/generate_personas.py --count 20000 --seed 42 \
        --out data/generated/personas.jsonl
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vo_personas_simulation.generation.population import (IncoherentPersona, generate_population,  # noqa: E402
                                                           write_jsonl)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=100, help="number of personas (default: 100)")
    parser.add_argument("--seed", type=int, default=42, help="simulation seed (default: 42)")
    parser.add_argument("--reference-date", default="2026-09-01T00:00:00Z",
                        help="UTC start of the week in which snapshot contexts are placed")
    parser.add_argument("--out", type=Path, default=Path("data/generated/personas.jsonl"))
    args = parser.parse_args(argv)

    reference = datetime.fromisoformat(args.reference_date.replace("Z", "+00:00")).astimezone(timezone.utc)
    try:
        n = write_jsonl(generate_population(args.count, args.seed, reference), args.out)
    except IncoherentPersona as exc:
        print(f"Incoherent persona: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {n} personas to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
