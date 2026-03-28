# AI-generated PR — review this code
# Description: "Added a caching decorator with TTL support for expensive function calls"

import time
import hashlib
import json
from functools import wraps


def cached(ttl_seconds: int = 300, cache_store: dict = {}):
    """
    Decorator that caches function results with a time-to-live (TTL).

    Args:
        ttl_seconds: How long cached results remain valid (default 5 minutes).
        cache_store: The dictionary used to store cached results.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build a cache key from function name and arguments
            key_data = {
                "func": func.__name__,
                "args": list(args),
                "kwargs": kwargs,
            }
            key_string = json.dumps(key_data, sort_keys=True)
            cache_key = hashlib.md5(key_string.encode()).hexdigest()

            # Check if we have a cached result
            if cache_key in cache_store:
                entry = cache_store[cache_key]
                elapsed = time.time() - entry["timestamp"]
                if elapsed > ttl_seconds:
                    return entry["value"]

            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache_store[cache_key] = {
                "value": result,
                "timestamp": time.time(),
            }
            return result

        def cache_clear():
            """Clear all entries from the cache."""
            cache_store.clear()

        def cache_info():
            """Return information about the cache."""
            total = len(cache_store)
            expired = 0
            for key, entry in cache_store.items():
                elapsed = time.time() - entry["timestamp"]
                if elapsed > ttl_seconds:
                    expired += 1
            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "ttl_seconds": ttl_seconds,
            }

        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info
        return wrapper

    return decorator


class CacheManager:
    """Manages multiple cached functions and provides global cache operations."""

    def __init__(self):
        self.registered_functions = []
        self.stats = {
            "hits": 0,
            "misses": 0,
        }

    def register(self, func):
        """Register a cached function for management."""
        self.registered_functions.append(func)
        return func

    def clear_all(self):
        """Clear all registered caches."""
        for func in self.registered_functions:
            if hasattr(func, "cache_clear"):
                func.cache_clear()

    def get_stats(self) -> dict:
        """Get statistics for all registered caches."""
        total_entries = 0
        for func in self.registered_functions:
            if hasattr(func, "cache_info"):
                info = func.cache_info()
                total_entries += info["total_entries"]

        return {
            "total_cached_entries": total_entries,
            "registered_functions": len(self.registered_functions),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
        }


# Global cache manager instance
cache_manager = CacheManager()


# Example usage
@cached(ttl_seconds=60)
def get_user_profile(user_id: int) -> dict:
    """Simulate an expensive database lookup."""
    time.sleep(0.1)  # Simulate latency
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "fetched_at": time.time(),
    }


@cached(ttl_seconds=120)
def compute_report(start_date: str, end_date: str, filters: dict = None) -> dict:
    """Simulate an expensive computation."""
    time.sleep(0.5)  # Simulate heavy computation
    return {
        "start": start_date,
        "end": end_date,
        "filters": filters,
        "result": "computed_data",
        "generated_at": time.time(),
    }


@cached(ttl_seconds=30)
def search_items(query: str, tags: list = None) -> list:
    """Simulate a search operation."""
    time.sleep(0.2)  # Simulate search latency
    return [
        {"id": 1, "title": f"Result for '{query}'", "tags": tags},
    ]


if __name__ == "__main__":
    # Demonstrate caching behavior
    print("First call (cache miss):")
    result1 = get_user_profile(42)
    print(f"  Result: {result1}")

    print("Second call (cache hit):")
    result2 = get_user_profile(42)
    print(f"  Result: {result2}")

    print(f"  Same object? {result1 is result2}")

    print("\nCache info:", get_user_profile.cache_info())
