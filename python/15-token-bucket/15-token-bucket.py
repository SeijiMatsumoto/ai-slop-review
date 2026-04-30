# Review this code — find bugs, understand the logic, complete the TODOs

import time
from typing import Callable


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens += elapsed * self.refill_rate
        self.last_refill = now

    def consume(self, amount: float) -> bool:
        self._refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def available(self) -> float:
        return self.tokens


def rate_limited(bucket: TokenBucket, cost: float = 1.0) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if not bucket.consume(cost):
                raise RuntimeError(
                    f"Rate limit exceeded: insufficient tokens (need {cost}, "
                    f"have {bucket.tokens:.2f})"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# TODO: Add a wait_and_consume(amount, timeout) method that blocks (using time.sleep
#       in a loop) until tokens are available or timeout expires, returns True/False
# TODO: Add support for multiple named buckets with different rates that all must pass
#       for a request to proceed (AND-logic across buckets)


if __name__ == "__main__":
    print("=== TokenBucket basic usage ===")
    bucket = TokenBucket(capacity=10.0, refill_rate=2.0)  # 2 tokens/sec, max 10

    print(f"  Initial tokens: {bucket.available():.2f}")

    results = []
    for i in range(12):
        ok = bucket.consume(1.0)
        results.append(ok)
        print(f"  consume(1.0) -> {ok} (tokens remaining: {bucket.tokens:.2f})")

    print(f"\n  Consumed {sum(results)} out of 12 attempts")

    print("\n=== Token refill (sleep 2s) ===")
    time.sleep(2)
    avail = bucket.available()
    print(f"  available() after 2s sleep: {avail:.2f}")
    actual = bucket.tokens
    bucket._refill()
    print(f"  Actual after manual _refill(): {bucket.tokens:.2f}")

    print("\n=== Overflow demonstration ===")
    bucket2 = TokenBucket(capacity=5.0, refill_rate=10.0)
    bucket2.tokens = 5.0
    time.sleep(2)
    bucket2._refill()
    print(f"  After 2s at 10 tokens/sec (cap=5): tokens={bucket2.tokens:.2f}")

    print("\n=== rate_limited decorator ===")
    api_bucket = TokenBucket(capacity=3.0, refill_rate=1.0)

    @rate_limited(api_bucket, cost=1.0)
    def call_api(endpoint: str) -> str:
        return f"Response from {endpoint}"

    for i in range(5):
        try:
            result = call_api(f"/api/endpoint/{i}")
            print(f"  Call {i+1}: {result}")
        except RuntimeError as e:
            print(f"  Call {i+1}: RATE LIMITED — {e}")
