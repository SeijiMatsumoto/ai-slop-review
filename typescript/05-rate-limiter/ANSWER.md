# 08 — Rate Limiter (TypeScript/Next.js Middleware)

**Categories:** Logic error, Security, Architecture

1. **In-memory `Map` resets on serverless cold starts** — In serverless environments (Vercel, Lambda), each instance has its own memory. Rate limits don't persist across instances or restarts. Need Redis or similar external store.
2. **IP spoofable via `x-forwarded-for`** — Client can set this header to bypass rate limiting. Should be set/trusted only from the load balancer/CDN.
3. **Off-by-one: rate limit triggers on `>=` instead of `>`** — `count >= MAX_REQUESTS` blocks on the 100th request. The 100th request should be allowed (limit of 100 means 100 requests allowed, not 99).
4. **API key leaked in error message** — Line 106 returns `Invalid API key: ${apiKey}` — echoing the submitted key back. This could be logged, cached by proxies, or help attackers confirm partial keys.
5. **Cleanup iterates entire map on every request** — `cleanupExpiredEntries` runs on every request and iterates all entries. Under heavy load this is O(n) per request.
