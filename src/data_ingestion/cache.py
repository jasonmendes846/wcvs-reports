"""
Disk-backed cache for WCVS market data with TTL support.
"""

import json
import time
from pathlib import Path
from typing import Any, Optional, Tuple

DEFAULT_TTL_SECONDS = 86400  # 24 hours


class DataCache:
    """Simple JSON disk cache with TTL."""

    def __init__(self, cache_path: Path, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.cache_path = Path(cache_path)
        self.ttl_seconds = ttl_seconds
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, default=str)

    def get(self, key: str) -> Tuple[Optional[Any], bool]:
        """Return (value, is_stale). If missing, return (None, False)."""
        entry = self._data.get(key)
        if entry is None:
            return None, False
        timestamp = entry.get("timestamp", 0)
        age = time.time() - timestamp
        is_stale = age > self.ttl_seconds
        return entry.get("value"), is_stale

    def set(self, key: str, value: Any, source: str = "unknown") -> None:
        self._data[key] = {
            "value": value,
            "timestamp": time.time(),
            "source": source,
        }
        self._save()

    def keys(self):
        return self._data.keys()

    def clear(self) -> None:
        self._data = {}
        self._save()
