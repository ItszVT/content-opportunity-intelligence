"""Disk cache for every HTTP source in the project.

Design notes (§5, §6):
  - Keyed on a hash of the request's identifying material, not the URL, so
    secrets never touch a filename.
  - Cached responses live in data/raw/, which is gitignored and treated as
    disposable. Deleting the cache must never lose information -- anything
    that matters is promoted to data/frozen/ or data/snapshots/.
  - TTL is per-call, not global: TMDB /discover changes daily, static
    metadata never does, Wikipedia history for a past date is immutable.

Usage:
    cache = DiskCache("tmdb")
    hit = cache.get({"endpoint": "/discover/tv", "params": params}, ttl=TTL_24H)
    if hit is None:
        payload = <make the request>
        cache.set({"endpoint": "/discover/tv", "params": params}, payload)
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# --- TTL constants -----------------------------------------------------------

TTL_24H = 60 * 60 * 24
TTL_7D = 60 * 60 * 24 * 7
TTL_NEVER = None  # cached forever; use for immutable data

CACHE_ROOT = Path(os.getenv("CACHE_DIR", "data/raw/cache"))

# Key material is written to disk in plaintext for auditability, so refuse
# anything that looks like a credential before it gets there.
_SECRET_HINTS = ("token", "api_key", "apikey", "authorization", "secret", "password")


class CacheKeyError(ValueError):
    """Raised when key material looks like it contains a credential."""


class DiskCache:
    """A namespaced JSON cache on local disk."""

    def __init__(self, namespace: str, root: Optional[Path] = None) -> None:
        self.namespace = namespace
        self.root = (root or CACHE_ROOT) / namespace
        self.root.mkdir(parents=True, exist_ok=True)

    # --- internals ---

    @staticmethod
    def _assert_no_secrets(key_material: dict) -> None:
        def walk(obj: Any) -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(hint in str(k).lower() for hint in _SECRET_HINTS):
                        raise CacheKeyError(
                            f"Refusing to cache on key material containing {k!r}. "
                            "Auth belongs in headers, never in the cache key."
                        )
                    walk(v)
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    walk(item)

        walk(key_material)

    def _hash(self, key_material: dict) -> str:
        self._assert_no_secrets(key_material)
        canonical = json.dumps(
            key_material, sort_keys=True, separators=(",", ":"), default=str
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def path_for(self, key_material: dict) -> Path:
        return self.root / f"{self._hash(key_material)}.json"

    # --- public API ---

    def get(self, key_material: dict, ttl: Optional[int] = TTL_24H) -> Optional[Any]:
        """Return the cached payload, or None on miss or expiry."""
        path = self.path_for(key_material)
        if not path.exists():
            return None

        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # A corrupt entry is a miss, not a crash.
            return None

        if ttl is not None:
            cached_at = datetime.fromisoformat(entry["cached_at"])
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            if age > ttl:
                return None

        return entry["payload"]

    def set(self, key_material: dict, payload: Any) -> Path:
        """Write a payload to the cache. Returns the path written."""
        path = self.path_for(key_material)
        entry = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "namespace": self.namespace,
            "key_material": key_material,  # stored so a cache file is auditable
            "payload": payload,
        }
        # Write to a temp file then rename, so an interrupted write can't
        # leave a half-written entry that later reads as a valid hit.
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entry, default=str), encoding="utf-8")
        tmp.replace(path)
        return path

    def clear(self) -> int:
        """Delete every entry in this namespace. Returns the count removed."""
        removed = 0
        for path in self.root.glob("*.json"):
            path.unlink()
            removed += 1
        return removed


if __name__ == "__main__":
    cache = DiskCache("_selftest")
    key = {"endpoint": "/demo", "params": {"page": 1}}

    assert cache.get(key) is None, "expected a miss on a fresh key"
    cache.set(key, {"results": [1, 2, 3]})
    assert cache.get(key) == {"results": [1, 2, 3]}, "expected a hit"
    assert cache.get(key, ttl=0) is None, "expected expiry at ttl=0"
    assert cache.get({"endpoint": "/demo", "params": {"page": 2}}) is None

    try:
        cache.set({"api_key": "leak"}, {})
    except CacheKeyError:
        pass
    else:
        raise AssertionError("secret guard did not fire")

    cache.clear()
    print("cache.py: all checks passed")