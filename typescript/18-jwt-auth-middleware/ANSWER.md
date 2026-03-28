# 18 — JWT Auth Middleware (TypeScript)

**Categories:** Security, Authentication, Token Validation, Timing Attacks

## Bug 1: Sensitive Data Stored in JWT Payload

The `JWTPayload` interface includes `password`, and `generateToken()` puts the user's password directly into the JWT payload. JWTs are base64-encoded (not encrypted), so anyone who intercepts or inspects the token can read the user's password in plain text. The `refreshMiddleware` also round-trips the password back into a new token, perpetuating the exposure.

**Fix:** Never include secrets in JWT payloads. Remove `password` from `JWTPayload` and `generateToken()`:

```typescript
const payload = {
  userId: user.id,
  email: user.email,
  role: user.role,
};
```

## Bug 2: Algorithm Confusion — Uses `jwt.decode()` Instead of `jwt.verify()`

The `authMiddleware` calls `jwt.decode(token)` (line ~93), which does **not** verify the signature at all. It simply base64-decodes the token. The code then attempts a manual HMAC-SHA256 signature check, but this is fundamentally broken because it assumes the algorithm is always HS256. An attacker can craft a token with `"alg": "none"` and an empty signature, or use RS256 with the public key as the HMAC secret. The `verifyToken()` function correctly uses `jwt.verify()` but is never called in the middleware.

**Fix:** Use `jwt.verify()` with an explicit algorithm whitelist:

```typescript
const payload = jwt.verify(token, config.secret, {
  algorithms: ["HS256"],
  issuer: config.issuer,
  audience: config.audience,
}) as JWTPayload;
```

## Bug 3: Issuer and Audience Not Validated

Although `config` defines `issuer` and `audience`, and `generateToken()` includes them when signing, the `authMiddleware` never checks these claims during verification. An attacker with a valid token from a different service using the same secret can authenticate against this API. The `verifyToken()` utility also doesn't validate issuer or audience.

**Fix:** Pass `issuer` and `audience` options to `jwt.verify()`:

```typescript
jwt.verify(token, config.secret, {
  issuer: config.issuer,
  audience: config.audience,
});
```

## Bug 4: Timing-Unsafe String Comparison for Signatures

The `compareSignatures()` function uses `===` for string comparison, which short-circuits on the first differing character. This leaks information about how many leading characters of the signature are correct, enabling a timing side-channel attack where an attacker can brute-force the signature one character at a time.

**Fix:** Use `crypto.timingSafeEqual()`:

```typescript
function compareSignatures(provided: string, expected: string): boolean {
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length) {
    return false;
  }
  return crypto.timingSafeEqual(a, b);
}
```

(Though ideally, remove the manual signature check entirely and use `jwt.verify()`.)

## Bug 5: Token Expiry Compared Against `Date.now()` (Milliseconds vs. Seconds)

The expiry check `payload.exp < Date.now()` compares a JWT `exp` claim (which is in **seconds** since epoch, per the JWT spec) against `Date.now()` (which returns **milliseconds**). This means the check effectively never triggers because a seconds-based timestamp is always smaller than a milliseconds-based one. Every token appears expired immediately, but this bug is masked because the `catch` block swallows the logic and returns a generic 401.

**Fix:** Compare in the same unit:

```typescript
if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
  return res.status(401).json({ error: "Token expired" });
}
```

## Bug 6: Catch-All Returns Generic 401 for All Errors

The `catch` block in `authMiddleware` catches every possible error (network issues, JSON parse failures, expired tokens, invalid signatures) and returns the same `{ error: "Authentication failed" }` response with a 401 status. This makes debugging impossible and conflates authorization failures (403) with authentication failures (401). A role mismatch should return 403 Forbidden, not 401 Unauthorized.

**Fix:** Handle different error types distinctly:

```typescript
catch (error) {
  if (error instanceof jwt.TokenExpiredError) {
    return res.status(401).json({ error: "Token expired" });
  }
  if (error instanceof jwt.JsonWebTokenError) {
    return res.status(401).json({ error: "Invalid token" });
  }
  return res.status(500).json({ error: "Internal server error" });
}
```

And for the role check, return 403:

```typescript
if (requiredRole && payload.role !== requiredRole) {
  return res.status(403).json({ error: "Insufficient permissions" });
}
```
