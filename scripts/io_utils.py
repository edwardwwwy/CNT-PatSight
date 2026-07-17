from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    """Return a stable, second-precision UTC timestamp."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def unique_part_path(path: Path) -> Path:
    """Return a process- and attempt-unique temporary sibling path."""
    return path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.part")


def replace_with_retry(temporary: Path, target: Path, attempts: int = 20) -> None:
    """Atomically publish a file despite short-lived Windows reader locks."""
    last_error: OSError | None = None
    for attempt in range(attempts):
        try:
            os.replace(temporary, target)
            return
        except OSError as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(min(0.05 * (attempt + 1), 0.5))
    temporary.unlink(missing_ok=True)
    assert last_error is not None
    raise last_error


def atomic_write_text(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Write text to a unique sibling and atomically publish it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = unique_part_path(path)
    try:
        temporary.write_text(text, encoding=encoding)
        replace_with_retry(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_json(path: Path, value: Any) -> None:
    """Publish UTF-8 JSON without exposing partial content to readers."""
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
    )
