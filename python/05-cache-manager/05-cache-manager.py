# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   TTL (time-to-live): how long a cached entry stays valid before it expires
#   LRU (least recently used): eviction policy — when cache is full, remove the entry
#     that was accessed least recently to make room for a new one
#   Hit rate: hits / (hits + misses) — measure of cache effectiveness

import time
from dataclasses import dataclass


@dataclass
class CacheEntry:
    key: str
    value: object
    created_at: float
    last_accessed: float


class CacheManager:
    def __init__(self, max_size: int = 100, ttl_seconds: float = 300.0) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def _is_expired(self, entry: CacheEntry) -> bool:
        return time.monotonic() - entry.created_at < self.ttl_seconds

    def _evict_lru(self) -> None:
        if not self._store:
            return
        lru_key = max(self._store, key=lambda k: self._store[k].last_accessed)
        del self._store[lru_key]

    def get(self, key: str) -> object:
        entry = self._store.get(key)
        if entry is None or self._is_expired(entry):
            if entry is not None:
                del self._store[key]
            self._misses += 1
            return None
        entry.last_accessed = time.monotonic()
        self._hits += 1
        return entry.value

    def set(self, key: str, value: object) -> None:
        if len(self._store) >= self.max_size and key not in self._store:
            self._evict_lru()
        now = time.monotonic()
        self._store[key] = CacheEntry(key=key, value=value, created_at=now, last_accessed=now)

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "size": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }


# TODO: Add a get_or_set(key: str, factory_fn: Callable) -> object method that returns
#       the cached value if present and unexpired, otherwise calls factory_fn(), stores
#       the result under key, and returns it
# TODO: Add a clear_expired() -> int method that removes all expired entries and returns
#       the count of entries removed


if __name__ == "__main__":
    cache = CacheManager(max_size=3, ttl_seconds=5.0)

    print("=== Basic set/get ===")
    cache.set("user:1", {"name": "Alice"})
    cache.set("user:2", {"name": "Bob"})
    cache.set("user:3", {"name": "Charlie"})

    print(f"  get user:1 -> {cache.get('user:1')}")
    print(f"  get user:2 -> {cache.get('user:2')}")
    print(f"  get missing -> {cache.get('user:99')} (expected None)")
    print(f"  Stats: {cache.stats()}")

    print("\n=== LRU eviction (max_size=3, adding 4th) ===")
    # user:1 and user:2 were accessed; user:3 was not — it should be evicted
    cache.set("user:4", {"name": "Diana"})
    print(f"  user:3 (LRU) should be evicted: {cache.get('user:3')} (expected None)")
    print(f"  user:4 should exist: {cache.get('user:4')}")

    print("\n=== TTL expiry ===")
    cache2 = CacheManager(max_size=10, ttl_seconds=2.0)
    cache2.set("temp", "expires soon")
    print(f"  Immediately: {cache2.get('temp')} (expected 'expires soon')")
    time.sleep(3)
    print(f"  After 3s: {cache2.get('temp')} (expected None)")

    print("\n=== Final stats ===")
    print(f"  {cache.stats()}")
