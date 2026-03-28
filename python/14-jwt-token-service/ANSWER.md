# 14 — JWT Token Service (Python)

**Categories:** Security, Authentication, Cryptography

## Bug 1: Hardcoded Weak Secret Key

`SECRET_KEY = "jwt-secret-2024"` is hardcoded directly in the source code and is trivially guessable. Anyone with access to the codebase (or who guesses the secret) can forge arbitrary tokens for any user, including admin accounts.

**Fix:** Load the secret from an environment variable and use a cryptographically random value:

```python
import os
SECRET_KEY = os.environ["JWT_SECRET_KEY"]  # Set to a long random string in production
```

## Bug 2: Algorithm Confusion — `"none"` Algorithm Allowed

In `verify_token`, the `algorithms` parameter includes `"none"`:

```python
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256", "none"])
```

The `"none"` algorithm means the token has no signature at all. An attacker can craft a token with `"alg": "none"`, remove the signature, and the server will accept it as valid without any secret key. This completely bypasses authentication.

**Fix:** Only allow the specific algorithm you use for signing:

```python
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

## Bug 3: Access Token Expiry Uses Seconds Instead of Minutes

The config says `ACCESS_TOKEN_EXPIRY = 15  # minutes`, but `create_access_token` passes it as seconds:

```python
"exp": datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRY),
```

This means tokens expire in 15 seconds, not 15 minutes. Users will constantly get "token expired" errors and be confused. The `expires_in` field in the login response also returns `15`, which the client will interpret incorrectly.

**Fix:** Use `timedelta(minutes=ACCESS_TOKEN_EXPIRY)`.

## Bug 4: Refresh Tokens Never Expire

The `create_refresh_token` function stores `created_at` but the refresh endpoint never checks the token's age. Even though `REFRESH_TOKEN_EXPIRY = 30` is defined, it is never used anywhere. A refresh token is valid forever once created, so a stolen refresh token grants permanent access.

**Fix:** Check the age of the refresh token before issuing a new access token:

```python
created_at = token_data["created_at"]
if time.time() - created_at > REFRESH_TOKEN_EXPIRY * 86400:
    del refresh_tokens[token_id]
    return jsonify({"error": "Refresh token expired"}), 401
```

## Bug 5: Blacklist Checked After Validation, Not Before

In the `/protected` endpoint, the token is first decoded via `verify_token`, and only after that is `is_token_blacklisted` called. This means a blacklisted token is still fully decoded and its payload is processed before the blacklist check. If there were any side effects during decoding or if the validation logic short-circuits on error before reaching the blacklist check, revoked tokens could still be used. The check order should be reversed: check the blacklist first, then validate.

**Fix:** Check the blacklist before decoding:

```python
token = auth_header.split(" ")[1]

if is_token_blacklisted(token):
    return jsonify({"error": "Token has been revoked"}), 401

payload = verify_token(token)
if not payload:
    return jsonify({"error": "Invalid or expired token"}), 401
```

## Bug 6: Refresh Tokens Not Invalidated on Logout

The `/auth/logout` endpoint only blacklists the access token. The associated refresh token remains valid, so after "logging out," an attacker (or the user) can immediately use the refresh token to get a new access token, making logout effectively useless.

**Fix:** Accept and invalidate the refresh token during logout as well, or delete it from the `refresh_tokens` store.
