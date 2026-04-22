"""Import production-like payment events from local JSONL files.

Usage:
  python -m app.scripts.ingest_events data/examples/payment_events.jsonl
  python -m app.scripts.ingest_events data/examples/payment_events.jsonl --run-pipeline
"""
import argparse
import asyncio
from pathlib import Path

import orjson

from app.api.routes_system import _coerce_payment_event
from app.pipeline import process_order
from app.storage import orders_repo
from app.storage.bootstrap import ensure_initialized


async def _import_file(path: Path, run_pipeline: bool) -> dict:
    ensure_initialized()
    imported = 0
    failed = 0
    errors: list[str] = []

    with path.open("rb") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = orjson.loads(line)
                order = _coerce_payment_event(payload)
                orders_repo.update(order)
                if run_pipeline:
                    await process_order(order)
                imported += 1
            except Exception as e:
                failed += 1
                errors.append(f"line {line_no}: {e}")

    return {"ok": failed == 0, "path": str(path), "imported": imported, "failed": failed, "errors": errors[:10]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import local payment event JSONL into storage/runtime/orders.jsonl")
    parser.add_argument("path", nargs="?", default="data/examples/payment_events.jsonl")
    parser.add_argument("--run-pipeline", action="store_true", help="Run the full 9-stage pipeline after each import")
    args = parser.parse_args()

    result = asyncio.run(_import_file(Path(args.path), args.run_pipeline))
    print(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode("utf-8"))


if __name__ == "__main__":
    main()
