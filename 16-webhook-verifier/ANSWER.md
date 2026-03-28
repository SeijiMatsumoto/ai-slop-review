# Problem 16: Webhook Verifier — Bugs

## Bug 1: Timing Attack on Signature Comparison (Security — Critical)

**Line:** `if (signatureParts["v1"] === expectedSignature)`

The code uses `===` to compare the expected HMAC signature with the one provided in the header. Standard string comparison short-circuits on the first mismatched character, leaking timing information about how many leading characters are correct. An attacker can iteratively guess the correct signature one byte at a time.

**Fix:** Use `crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b))` to compare signatures in constant time.

---

## Bug 2: No Replay Protection (Security — High)

**Location:** `verifySignature` function and `/webhooks/stripe` handler

The `stripe-signature` header includes a `t=` timestamp component, but the code completely ignores it. Stripe includes this so consumers can reject events older than a tolerance window (e.g., 5 minutes). Without this check, an attacker who intercepts a valid webhook can replay it indefinitely.

**Fix:** Parse the `t` value from the signature header, compare it to the current time, and reject events outside an acceptable tolerance window (e.g., 300 seconds).

---

## Bug 3: HMAC Constructed Incorrectly (Correctness — Critical)

**Line:** `crypto.createHmac("sha256", secret).update(payload).digest("hex")`

The `computeSignature` function signs only the raw body. Stripe's actual signature scheme signs `${timestamp}.${payload}` — i.e., the timestamp and body concatenated with a dot. This means the signature computed here will never match a real Stripe signature, so all legitimate webhooks will be rejected (and the verification is weaker since it doesn't bind the timestamp to the signature).

**Fix:** Change to `crypto.createHmac("sha256", secret).update(`${timestamp}.${payload}`).digest("hex")` and pass the timestamp from the header.

---

## Bug 4: Secret Hardcoded in Source (Security — Critical)

**Line:** `const STRIPE_WEBHOOK_SECRET = "whsec_5f3KqR8vT2mN7xJdL9pY4wA6bC0eHgUi";`

The webhook signing secret is hardcoded directly in the source file. Anyone with access to the repository (including all developers, CI systems, and anyone who ever had access) can see the secret. If the repo is public, the secret is fully exposed.

**Fix:** Load from an environment variable: `const STRIPE_WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET!` and ensure it's set in the deployment environment.

---

## Bug 5: No Idempotency / Duplicate Event Protection (Reliability — High)

**Location:** `processEvent` function and `/webhooks/stripe` handler

The code processes every event it receives without checking if the event ID (`event.id`) has been seen before. Stripe explicitly documents that webhooks may be delivered more than once. Without tracking processed event IDs (e.g., in a database or Redis set), replayed or redelivered events will trigger duplicate side effects — double emails, duplicate provisioning, etc.

**Fix:** Before calling `processEvent`, check if `event.id` exists in a persistent store of processed events. If it does, return 200 immediately without reprocessing. After successful processing, record the event ID.
