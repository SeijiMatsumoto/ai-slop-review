# OAuth Callback Handler — Bugs

## Bug 1: Missing `state` Parameter Check (CSRF)
**Location:** `/auth/google/callback` handler (line ~96)

The `/auth/google/login` route correctly generates a random `state` parameter and stores it in the session. However, the callback handler **never checks** the `state` parameter from the query string against `req.session.oauthState`. This means an attacker can craft a callback URL with their own authorization code and trick a victim into visiting it, linking the attacker's Google account to the victim's session (a CSRF attack on the OAuth flow).

## Bug 2: Token Stored in localStorage (XSS Risk)
**Location:** The `<script>` block in the HTML response (line ~119)

The access token and refresh token are stored in `localStorage` via `localStorage.setItem('auth_tokens', ...)`. Unlike httpOnly cookies, localStorage is accessible to **any JavaScript** running on the same origin. A single XSS vulnerability anywhere on the domain allows an attacker to steal both the access and refresh tokens. Tokens should be stored in httpOnly, secure cookies instead.

## Bug 3: Redirect URI Not Validated (Open Redirect)
**Location:** `const redirectTarget = typeof redirect_to === "string" ? redirect_to : "/dashboard";` (line ~122)

The `redirect_to` query parameter is used directly as the post-login redirect destination without any validation. An attacker can set `redirect_to=https://evil-phishing-site.com/fake-login` and share the link. After the user successfully authenticates, they are redirected to the attacker's site, which could impersonate the real app to steal credentials. The fix is to validate that `redirect_to` is a relative path or belongs to an allowed list of domains.

## Bug 4: Access Token Logged
**Location:** `console.log("Token exchange successful:", tokens);` (line ~104)

The full token response object — including `access_token`, `refresh_token`, and `id_token` — is logged to the console. In production, console output typically goes to log aggregation services (CloudWatch, Datadog, etc.) where it may be accessible to many engineers or even stored in plaintext. This leaks sensitive credentials. The log line should be removed or redacted.

## Bug 5: No Token Expiry Handling
**Location:** `upsertUser` and the token payload sent to the frontend

The `TokenResponse` interface includes `expires_in` (typically 3600 seconds for Google), but this value is **never stored or used**. The `upsertUser` function stores `accessToken` without any expiry timestamp. The frontend payload also omits `expires_in`. This means the application will continue using the access token long after it expires (1 hour), resulting in API failures. The fix is to compute and store an `expiresAt` timestamp and implement token refresh logic.
