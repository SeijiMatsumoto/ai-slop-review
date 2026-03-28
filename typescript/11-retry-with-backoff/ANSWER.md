# Problem 20: Retry With Backoff — Bugs

## Bug 1: Retries Non-Idempotent Requests (Correctness — Critical)

**Location:** `fetchWithRetry` function and convenience methods `post`, `put`, `del`

The retry logic applies uniformly to all HTTP methods, including POST, PUT, and DELETE. These are not idempotent — retrying a POST that creates an order or charges a payment can cause duplicate side effects (double charges, duplicate records). The convenience methods `post()`, `put()`, and `del()` all funnel through `fetchWithRetry` with no safety check.

**Fix:** By default, only retry idempotent methods (GET, HEAD, OPTIONS). For non-idempotent methods, either skip retrying or require the caller to explicitly opt in with a flag like `retryNonIdempotent: true`.

---

## Bug 2: No Jitter Causes Thundering Herd (Reliability — High)

**Line:** `return baseDelayMs * Math.pow(2, attempt);` in `calculateDelay`

The delay is purely deterministic: 1s, 2s, 4s, 8s, etc. When a server goes down and comes back up, all clients will retry at exactly the same intervals, creating a thundering herd that can immediately overwhelm the recovering server.

**Fix:** Add random jitter to the delay. A common approach is "full jitter": `Math.random() * baseDelayMs * Math.pow(2, attempt)`. Or use "decorrelated jitter" for even better distribution.

---

## Bug 3: Retries on 400-Level Client Errors (Correctness — Medium)

**Location:** `makeRequest` throws on any `!response.ok`, and `fetchWithRetry` retries all errors

The code throws an error for any non-2xx status code (via `!response.ok`), and the retry loop catches all errors indiscriminately. This means 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), and 422 (Unprocessable Entity) are all retried. These are client errors that will never succeed on retry — the request itself is wrong.

**Fix:** Only retry on 5xx server errors and 429 (rate limit). For 4xx errors, throw immediately without retrying. Check `(error as any).status >= 500 || (error as any).status === 429` before deciding to retry.

---

## Bug 4: Timeout Resets on Each Retry (Reliability — Medium)

**Location:** `makeRequest` is called with `opts.timeoutMs` on each attempt

Each retry attempt gets a fresh timeout of `timeoutMs` (default 10 seconds). With 3 retries and exponential backoff delays, the total wall-clock time can be: `10s + 1s + 10s + 2s + 10s + 4s + 10s = 47 seconds`. The caller likely expects the operation to complete within a bounded total time, not per-attempt.

**Fix:** Implement an overall deadline/timeout that encompasses all retry attempts. Create a single `AbortController` at the start and pass it through, or track elapsed time and reduce the per-request timeout on each attempt.

---

## Bug 5: Swallows the Original Error (Debugging — Medium)

**Line:** `throw new Error(`Max retries (${opts.maxRetries}) exceeded for ${config.url}`);`

When all retries are exhausted, the code throws a generic "Max retries exceeded" error, discarding `lastError` entirely. The actual HTTP status code, response body, and error details from the last (or any) attempt are lost. This makes debugging production issues extremely difficult — you only see "max retries exceeded" in logs with no indication of whether it was a 500, a timeout, or a connection reset.

**Fix:** Include the original error information. Use `Error.cause`: `throw new Error(`Max retries exceeded for ${config.url}`, { cause: lastError })`. Or attach the status and response to the error object so callers can inspect them.
