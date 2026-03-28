# 19 — Webhook Dispatcher (Python)

**Categories:** Security (SSRF), Secret Management, Reliability

## Bug 1: No URL Validation — SSRF Vulnerability

`register_endpoint` accepts any URL without validation. An attacker who can register webhook endpoints can point them at internal services:

```
http://169.254.169.254/latest/meta-data/  (AWS metadata)
http://localhost:6379/  (internal Redis)
http://10.0.0.1:8500/v1/kv/secrets  (internal Consul)
```

The server will make HTTP requests to these internal addresses on the attacker's behalf, leaking sensitive data or allowing access to internal services that are not exposed to the internet.

**Fix:** Validate and restrict URLs to allowed domains/schemes, and block private/reserved IP ranges:

```python
from urllib.parse import urlparse
import ipaddress

def _validate_url(self, url: str):
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise ValueError("Only HTTPS URLs are allowed")
    # Resolve hostname and check it's not a private IP
    ip = socket.gethostbyname(parsed.hostname)
    if ipaddress.ip_address(ip).is_private:
        raise ValueError("Internal URLs are not allowed")
```

## Bug 2: Secrets Logged in Plaintext

In `register_endpoint`, the webhook secret is logged:

```python
logger.info(f"Registered webhook endpoint: {endpoint_id} -> {url} (secret: {secret})")
```

And in `_deliver`, the full event payload (which may contain sensitive data like `payment_token` and `customer_email` in the example) is logged:

```python
logger.info(f"Delivering {event.event_type} to {endpoint_id}: URL={endpoint.url}, payload={json.dumps(payload)}")
```

With `logging.basicConfig(level=logging.DEBUG)`, all of this ends up in log files, which are often accessible by operations staff, log aggregation services, and potentially attackers who gain read access to logs.

**Fix:** Never log secrets. Redact or omit sensitive fields from payload logging:

```python
logger.info(f"Registered webhook endpoint: {endpoint_id} -> {url}")
logger.info(f"Delivering {event.event_type} to {endpoint_id}")
```

## Bug 3: No Exponential Backoff in Retry Logic

The retry logic uses a constant delay:

```python
RETRY_DELAY = 2  # seconds
# ...
time.sleep(self.RETRY_DELAY)
```

Every retry waits exactly 2 seconds. If an endpoint is down or overloaded, this hammers it with 5 requests in 10 seconds. For a dispatcher with many events, this creates a thundering herd problem and can make the receiving service's situation worse. It also blocks the calling thread for the entire retry sequence.

**Fix:** Use exponential backoff with jitter:

```python
import random
delay = self.RETRY_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 1)
time.sleep(delay)
```

## Bug 4: No Request Timeout — Hangs Forever

Neither `_deliver` nor `send_webhook` sets a timeout on `requests.post()`:

```python
response = requests.post(endpoint.url, json=payload, headers=headers)
```

If the receiving server accepts the TCP connection but never responds (e.g., it's stuck), this call will block indefinitely. Combined with the retry logic, a single unresponsive endpoint can block the entire dispatch thread forever.

**Fix:** Always set a timeout:

```python
response = requests.post(endpoint.url, json=payload, headers=headers, timeout=10)
```

## Bug 5: No HMAC Signature on Outgoing Webhooks

The `endpoint.secret` is stored for each webhook but never used. Outgoing webhook requests include no signature header (like `X-Webhook-Signature`). This means the receiving endpoint has no way to verify that the webhook actually came from this service and not from an attacker. The secret field exists but is completely non-functional.

**Fix:** Sign the payload with HMAC and include the signature in the request headers:

```python
import hmac
import hashlib

signature = hmac.new(
    endpoint.secret.encode(),
    json.dumps(payload).encode(),
    hashlib.sha256
).hexdigest()
headers["X-Webhook-Signature"] = f"sha256={signature}"
```
