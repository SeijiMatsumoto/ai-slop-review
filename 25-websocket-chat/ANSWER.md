# WebSocket Chat Server — Bugs

## Bug 1: No Authentication on Connection
**Location:** `wss.on("connection", ...)` handler (line ~109)

The server accepts any WebSocket connection without any authentication or authorization. There is no token verification, no session check, and no handshake validation. Anyone who knows the server address can connect, set any username (including impersonating other users via `set_username`), and join any room. The fix is to verify a JWT or session token during the WebSocket upgrade handshake (via the `req` parameter, e.g., checking cookies or an `Authorization` header).

## Bug 2: Messages Broadcast Without Sanitization (XSS)
**Location:** The `"message"` case in the message handler (lines ~148-159)

User-supplied `parsed.content` is placed directly into the `ChatMessage` and broadcast to all clients as-is. If a client sends `<script>alert('xss')</script>` as their message content, and the receiving clients render this in a browser using `innerHTML` or similar, it results in cross-site scripting. The server should sanitize or escape message content before broadcasting, or at minimum the protocol should ensure clients treat content as plain text.

## Bug 3: No Rate Limiting Per Socket
**Location:** The entire `ws.on("message", ...)` handler

There is no rate limiting on incoming messages. A malicious client can send thousands of messages per second, which the server will dutifully parse and broadcast to every client in the room. This can be used to:
- Denial-of-service the server (CPU exhaustion from JSON parsing and broadcasting)
- Flood other clients with messages
- Exhaust bandwidth

The fix is to implement per-socket rate limiting (e.g., a token bucket or sliding window counter) and disconnect or throttle clients that exceed the limit.

## Bug 4: Memory Leak from Never Removing Disconnected Clients
**Location:** `ws.on("close", ...)` handler (lines ~167-172)

When a client disconnects, the `close` handler calls `leaveRoom(client)` to remove them from their room, but it **never removes the client from the `clients` Map**. The line `clients.set(clientId, client)` adds every connection, but `clients.delete(clientId)` is never called. Over time, the `clients` Map grows unboundedly, leaking memory for every connection that has ever been made. The comment "client cleanup is handled by room leave" is incorrect — room leave only cleans up the room's Set, not the global `clients` Map.

## Bug 5: Room Names Not Validated
**Location:** The `"join"` case, line `const roomName = parsed.room` (line ~133)

Room names are taken directly from user input and used as Map keys without any validation beyond checking they are a non-empty string. This has several implications:
- A user could use `__proto__`, `constructor`, `toString`, or other special property names that may interfere with Map/object behavior in certain JavaScript contexts.
- Extremely long room names can waste memory.
- Room names with special characters, whitespace, or control characters can cause issues in logging, display, and downstream systems.

The fix is to validate room names against a whitelist pattern (e.g., alphanumeric plus hyphens, with a length limit).
