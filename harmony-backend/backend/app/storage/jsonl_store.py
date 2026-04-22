"""通用 JSONL 读写。每行一条 JSON 记录,append-only 友好。"""
from pathlib import Path
from typing import Iterator, List, Any
import orjson


def write_all(path: Path, records: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for r in records:
            f.write(orjson.dumps(r, option=orjson.OPT_APPEND_NEWLINE))


def read_all(path: Path) -> List[dict]:
    if not path.exists():
        return []
    out: List[dict] = []
    with path.open("rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(orjson.loads(line))
    return out


def append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as f:
        f.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE))


def iter_records(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with path.open("rb") as f:
        for line in f:
            line = line.strip()
            if line:
                yield orjson.loads(line)
