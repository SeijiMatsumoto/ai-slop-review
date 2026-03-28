# Answer: Password Reset Flow

## Bug 1: Token is `md5(email + timestamp)` — Guessable

The `generate_reset_token` function creates a token by hashing `email + timestamp` with MD5. Since the email is known to the attacker (they're the ones requesting the reset) and the timestamp is just the current Unix time in seconds, an attacker can brute-force the token by trying MD5 hashes for a range of timestamps around when they triggered the request. Even a 60-second window is only 60 attempts.

**Fix:** Use cryptographically secure random tokens:

```python
import secrets
token = secrets.token_urlsafe(32)
```

## Bug 2: No Token Expiry Check

The `password_reset_tokens` table stores a `created_at` timestamp, but the `confirm_reset` endpoint never checks it. A token generated months ago still works. This means if a reset email is found in an old inbox or leaked, it can be used indefinitely.

**Fix:** Check the token's age before allowing the reset:

```python
from datetime import datetime, timedelta

created_at = datetime.fromisoformat(reset_record["created_at"])
if datetime.utcnow() - created_at > timedelta(hours=1):
    return jsonify({"error": "Token has expired"}), 400
```

## Bug 3: No Rate Limiting on Reset Requests

The `/api/password-reset/request` endpoint has no rate limiting. An attacker can:
- Flood a user's inbox with hundreds of reset emails (email bombing)
- Enumerate valid email addresses by observing the different responses
- Cause load on the email infrastructure

**Fix:** Implement rate limiting per email and per IP:

```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@app.route("/api/password-reset/request", methods=["POST"])
@limiter.limit("3 per hour")
def request_reset():
    ...
```

## Bug 4: User Enumeration via Different Error Messages

The `request_reset` endpoint returns `"User not found"` with a 404 status for non-existent emails, and `"Reset email sent"` with a 200 for valid emails. This allows an attacker to enumerate which email addresses have accounts by observing the different responses.

**Fix:** Return the same response regardless of whether the email exists:

```python
# Always return success message
if user:
    token = generate_reset_token(email)
    # ... store token, send email ...

return jsonify({"message": "If an account exists with that email, a reset link has been sent."}), 200
```

## Bug 5: Password Stored with MD5

In `confirm_reset`, the new password is hashed with plain MD5: `hashlib.md5(new_password.encode()).hexdigest()`. MD5 is cryptographically broken for password storage — it has no salt, is extremely fast to brute-force, and pre-computed rainbow tables exist for it.

**Fix:** Use bcrypt, argon2, or scrypt:

```python
from werkzeug.security import generate_password_hash
password_hash = generate_password_hash(new_password, method="pbkdf2:sha256", salt_length=16)
```

Or use `bcrypt`:

```python
import bcrypt
password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
```

## Bug 6: Token Not Invalidated After Use

After a password is successfully reset in `confirm_reset`, the token remains in the database. The same token can be used repeatedly to reset the password again. If an attacker intercepts the token, they can keep resetting the password even after the legitimate user has already used it.

**Fix:** Delete the token (and ideally all tokens for that user) after successful reset:

```python
conn.execute(
    "DELETE FROM password_reset_tokens WHERE user_id = ?",
    (reset_record["user_id"],)
)
conn.commit()
```
