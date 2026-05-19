"""Export FastAPI's OpenAPI spec to `backend/app/api/openapi.json`.

Run after any API change:

    uv run python -m app.scripts.export_openapi

The committed JSON is the contract the frontend generates types from. CI in a
later phase will run this script in `--check` mode to detect drift.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.main import app

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "api" / "openapi.json"


def main() -> int:
    """Write or verify `backend/app/api/openapi.json`. Returns process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the committed file does not match the live spec.",
    )
    args = parser.parse_args()

    spec = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"

    if args.check:
        if not OUTPUT_PATH.exists():
            print(f"Expected {OUTPUT_PATH} to exist; run without --check to write it.")
            return 1
        committed = OUTPUT_PATH.read_text(encoding="utf-8")
        if committed != spec:
            print(
                "openapi.json drift detected; re-run `uv run python -m app.scripts.export_openapi`."
            )
            return 1
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(spec, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
