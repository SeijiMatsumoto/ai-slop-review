# Problem 18: Redis Session Store — Bugs

## Bug 1: Race Condition on Read-Modify-Write (Correctness — High)

**Location:** `updateSession` method

The method reads the session from Redis, modifies it in JavaScript, then writes it back. If two concurrent requests update the same session, one will overwrite the other's changes (last-write-wins). There is no Redis `WATCH`/`MULTI`/`EXEC` transaction or Lua script to make this atomic.

**Fix:** Use a Redis transaction with `WATCH` on the session key, or use a Lua script to perform the read-modify-write atomically on the Redis server.

---

## Bug 2: Session Fixation (Security — Critical)

**Location:** `loginHandler` function — `const sessionId = existingSessionId || uuidv4();`

When a user logs in, the code reuses the existing session ID from the cookie (`existingSessionId`) instead of always generating a new one. This enables session fixation attacks: an attacker sets a known session ID in the victim's browser (e.g., via a crafted link), waits for the victim to log in, and then uses that same session ID to access the authenticated session.

**Fix:** Always generate a new session ID on login: `const sessionId = uuidv4()`. Destroy the old session if one exists.

---

## Bug 3: JSON.parse on Untrusted Data With No Try/Catch (Reliability — Medium)

**Lines:** `JSON.parse(data)` in `getSession`, `getUserSessions`

If session data in Redis is corrupted, truncated, or manually modified, `JSON.parse` will throw a `SyntaxError` that is never caught. This will crash the request handler and return a 500 error. The `sessionMiddleware` also doesn't catch this, so a corrupted session crashes every request for that user.

**Fix:** Wrap `JSON.parse` calls in try/catch blocks. On parse failure, treat the session as invalid (delete it and return null).

---

## Bug 4: Session Data Includes Password Hash (Security — High)

**Lines:** `user: user` in `createSession` and `loginHandler`

The full `User` object, including the `passwordHash` field, is stored in the session data in Redis. This means the password hash is persisted in Redis, serialized/deserialized on every request, and potentially leaked if session data is ever exposed (logging, debugging, error messages). The `loginHandler` response correctly strips it, but the stored data retains it.

**Fix:** Exclude sensitive fields before storing: `const { passwordHash, ...safeUser } = user;` and store `safeUser` instead.

---

## Bug 5: No Session Expiry Enforced on Read (Security — Medium)

**Location:** `getSession` method and `sessionMiddleware`

A TTL is set when the session is created, but `getSession` never refreshes or validates the expiry. More critically, `updateSession` calls `this.client.set()` without re-setting the TTL via `expire`, so any update effectively removes the TTL and makes the session immortal. The middleware also doesn't refresh the TTL on access, so sessions that are actively used may expire while sessions that were updated once live forever.

**Fix:** After every `set` call, also call `expire` to reset the TTL. Alternatively, use `client.set(key, value, { EX: SESSION_TTL })` to atomically set the value and TTL together. Consider sliding window expiry by refreshing the TTL in `getSession` as well.
