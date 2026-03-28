# 16 — API Rate Limiter (Python/Flask)

**Categories:** Race Conditions, Security, Reliability

## Bug 1: TOCTOU Race Condition — Check and Increment Are Not Atomic

The rate limiter performs a `GET` to read the current count, checks if it exceeds the limit, then does a separate `INCR`. Between the `GET` and the `INCR`, another request from the same client can slip through. Under high concurrency, many requests can read the same count value and all pass the check before any of them increment it, allowing significantly more requests than the configured limit.

**Fix:** Use an atomic Redis operation. The standard pattern is to `INCR` first, then check the result:

```python
current_count = redis_client.incr(key)
if current_count == 1:
    redis_client.expire(key, window)
if current_count > max_requests:
    return jsonify({"error": "Rate limit exceeded"}), 429
```

Or use a Lua script to make the entire check-and-increment atomic.

## Bug 2: Trusting X-Forwarded-For Header

`get_client_ip()` blindly trusts the `X-Forwarded-For` header, which is trivially spoofable by any client. An attacker can send a different fake IP with every request to completely bypass rate limiting. This header should only be trusted when the request comes through a known reverse proxy.

**Fix:** Only trust `X-Forwarded-For` when the request comes from a trusted proxy IP, or use a library like `werkzeug.middleware.proxy_fix.ProxyFix` with a configured number of trusted proxies:

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
# Then just use request.remote_addr
```

## Bug 3: Redis Connection Failure Crashes the Application

If Redis is down or unreachable, every call to `redis_client.get()`, `redis_client.incr()`, etc. will raise a `redis.ConnectionError` exception. This means any endpoint with the `@rate_limit` decorator will return a 500 error when Redis is unavailable, effectively making the entire API go down because of a rate-limiting dependency.

**Fix:** Wrap Redis operations in a try/except and decide on a failure policy (fail open to allow requests, or fail closed to reject them):

```python
try:
    current = redis_client.get(key)
    # ... rate limit logic ...
except redis.ConnectionError:
    app.logger.warning("Redis unavailable, allowing request (fail-open)")
    return f(*args, **kwargs)
```

## Bug 4: Rate Limit Headers Leak Internal Information

The 429 response body includes `current_usage` (exact count) and `window` (exact window size), and every response includes an `X-RateLimit-ClientIP` header that reflects back the IP address used for rate limiting. This tells attackers exactly how the rate limiting works, what their detected IP is (useful for confirming spoofing works), and how to time their attacks to stay just under the limit.

**Fix:** Remove `X-RateLimit-ClientIP` and `current_usage` from responses. Keep only standard headers like `X-RateLimit-Remaining` and `Retry-After`.

## Bug 5: Window Expiry Race on First Request

When the first request comes in (`current is None`), the code does `redis_client.set(key, 1, ex=window)`. But between the `GET` that returned `None` and the `SET`, another concurrent request could also see `None` and also do `SET` with count 1. Both requests reset the window, and one of the increments is lost. This is another manifestation of the TOCTOU issue in Bug 1, but specifically affects window initialization — the expiry could be set twice, extending the window incorrectly.

**Fix:** Use the atomic `INCR` + conditional `EXPIRE` pattern described in Bug 1.
