# 18 — Cache Decorator (Python)

**Categories:** Memory Management, Thread Safety, Python Pitfalls

## Bug 1: Mutable Default Argument Shared Across All Decorated Functions

The decorator signature uses a mutable default argument:

```python
def cached(ttl_seconds: int = 300, cache_store: dict = {}):
```

In Python, default mutable arguments are created once and shared across all calls. This means every function decorated with `@cached()` without an explicit `cache_store` shares the same dictionary. If `get_user_profile` and `compute_report` are both decorated with `@cached(...)`, they write to the same dict. Calling `cache_clear()` on one function wipes the other function's cache too.

**Fix:** Use `None` as the default and create a new dict inside the function:

```python
def cached(ttl_seconds: int = 300, cache_store: dict = None):
    if cache_store is None:
        cache_store = {}
```

## Bug 2: TTL Check Is Inverted — Serves Stale Data Forever

The TTL check logic is backwards:

```python
if elapsed > ttl_seconds:
    return entry["value"]
```

This returns the cached value when the entry has *expired* (elapsed > TTL), and falls through to recompute when the entry is *still fresh*. The cache effectively does the opposite of what it should: it serves stale data and recomputes fresh data. Once an entry expires, it will be served forever because the recomputation branch always creates a fresh timestamp, which then immediately has `elapsed < ttl_seconds`, causing it to be ignored in favor of recomputation.

**Fix:** Invert the comparison:

```python
if elapsed < ttl_seconds:
    return entry["value"]
```

## Bug 3: Unbounded Cache Size — Memory Leak

There is no limit on how many entries can be stored in `cache_store`. Every unique combination of function arguments creates a new cache entry that is never evicted (even expired entries remain in the dict forever). Over time in a long-running application, this will consume all available memory.

**Fix:** Implement a maximum cache size with LRU eviction, or periodically clean up expired entries:

```python
MAX_CACHE_SIZE = 1000

if len(cache_store) >= MAX_CACHE_SIZE:
    # Evict oldest entries
    oldest_key = min(cache_store, key=lambda k: cache_store[k]["timestamp"])
    del cache_store[oldest_key]
```

## Bug 4: Not Thread-Safe

The cache dictionary is accessed and modified without any locking. In a multithreaded application (common with Flask, Django, etc.), two threads can simultaneously read and write to `cache_store`, leading to lost updates, corrupted state, or `RuntimeError: dictionary changed size during iteration` from the `cache_info` method which iterates over the dict.

**Fix:** Use a threading lock:

```python
import threading
lock = threading.Lock()

with lock:
    if cache_key in cache_store:
        ...
```

## Bug 5: Fails on Unhashable Arguments with Cryptic Error

The cache key is built by passing `args` and `kwargs` through `json.dumps`:

```python
key_data = {"func": func.__name__, "args": list(args), "kwargs": kwargs}
key_string = json.dumps(key_data, sort_keys=True)
```

This will raise a `TypeError` for any argument that isn't JSON-serializable: sets, custom objects, bytes, datetime objects, etc. The `search_items` function in the example takes `tags: list`, which works, but passing a set or a custom object will crash with an unhelpful error like `TypeError: Object of type set is not JSON serializable` with no indication that it came from the caching layer.

**Fix:** Use a more robust serialization strategy with a fallback, or catch the error and skip caching:

```python
try:
    key_string = json.dumps(key_data, sort_keys=True, default=str)
except TypeError:
    return func(*args, **kwargs)  # Skip caching for unhashable args
```
