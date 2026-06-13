"""
cache.py
--------
Developer-built: File-based TTL (Time-To-Live) cache for scraped content.
Avoids re-fetching the same URL within a configurable time window.
Saves API costs by caching AI results too.
No AI involved — pure caching infrastructure.
"""

import os
import json
import time
import hashlib
import logging
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Default cache settings
DEFAULT_CACHE_DIR = ".cache"
DEFAULT_TTL_SECONDS = 3600  # 1 hour


class FileCache:
    """
    Simple file-based key-value cache with TTL expiration.

    Files are stored as JSON in a local directory.
    Cache keys are URL-derived MD5 hashes.
    """

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR, ttl: int = DEFAULT_TTL_SECONDS):
        """
        Initialize the file cache.

        Args:
            cache_dir: Directory to store cache files.
            ttl: Time-to-live in seconds for each cache entry.
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[Cache] Initialized at '{cache_dir}' with TTL={ttl}s")

    def _make_key(self, identifier: str) -> str:
        """
        Convert a URL or string to a safe filename using MD5 hash.

        Args:
            identifier: URL or any string key.

        Returns:
            MD5 hex digest as cache key.
        """
        return hashlib.md5(identifier.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.json"

    def get(self, identifier: str) -> Optional[Any]:
        """
        Retrieve cached data if it exists and hasn't expired.

        Args:
            identifier: URL or string key to look up.

        Returns:
            Cached data, or None if not found / expired.
        """
        key = self._make_key(identifier)
        cache_file = self._cache_path(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                entry = json.load(f)

            timestamp = entry.get("timestamp", 0)
            age = time.time() - timestamp

            if age > self.ttl:
                logger.debug(f"[Cache] EXPIRED for {identifier[:60]}... (age: {age:.0f}s)")
                cache_file.unlink(missing_ok=True)  # Clean up expired file
                return None

            logger.info(f"[Cache] HIT for {identifier[:60]}... (age: {age:.0f}s)")
            return entry.get("data")

        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.warning(f"[Cache] Error reading cache for {identifier}: {e}")
            return None

    def set(self, identifier: str, data: Any) -> bool:
        """
        Store data in cache with current timestamp.

        Args:
            identifier: URL or string key.
            data: Any JSON-serializable data to cache.

        Returns:
            True on success, False on failure.
        """
        key = self._make_key(identifier)
        cache_file = self._cache_path(key)

        try:
            entry = {
                "key": identifier[:200],  # Store original key for debugging
                "timestamp": time.time(),
                "data": data,
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)

            logger.debug(f"[Cache] SET for {identifier[:60]}...")
            return True

        except (IOError, TypeError) as e:
            logger.error(f"[Cache] Failed to write cache for {identifier}: {e}")
            return False

    def invalidate(self, identifier: str) -> bool:
        """
        Manually invalidate (delete) a cache entry.

        Args:
            identifier: URL or string key to delete.

        Returns:
            True if entry was deleted, False if not found.
        """
        key = self._make_key(identifier)
        cache_file = self._cache_path(key)

        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"[Cache] Invalidated {identifier[:60]}...")
            return True
        return False

    def clear_all(self) -> int:
        """
        Delete all cache files.

        Returns:
            Number of files deleted.
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except IOError:
                pass
        logger.info(f"[Cache] Cleared {count} cache files")
        return count

    def clear_expired(self) -> int:
        """
        Delete only expired cache entries.

        Returns:
            Number of expired files deleted.
        """
        count = 0
        now = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                timestamp = entry.get("timestamp", 0)
                if now - timestamp > self.ttl:
                    cache_file.unlink()
                    count += 1
            except Exception:
                pass

        logger.info(f"[Cache] Cleared {count} expired cache files")
        return count

    def stats(self) -> dict:
        """
        Return cache statistics.

        Returns:
            Dict with total entries, size, and hit/miss counts.
        """
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files if f.exists())
        now = time.time()

        valid = 0
        expired = 0
        for cache_file in files:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                age = now - entry.get("timestamp", 0)
                if age <= self.ttl:
                    valid += 1
                else:
                    expired += 1
            except Exception:
                expired += 1

        return {
            "total_entries": len(files),
            "valid_entries": valid,
            "expired_entries": expired,
            "cache_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
            "ttl_seconds": self.ttl,
        }


# Default global cache instance
_default_cache: Optional[FileCache] = None


def get_cache(ttl: int = DEFAULT_TTL_SECONDS) -> FileCache:
    """Get or create the default global cache instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = FileCache(ttl=ttl)
    return _default_cache
