# 01 — User Lookup API (TypeScript/Next.js)

**Categories:** Missing null guards, Security

1. **No null check on `user`** — `findUnique` can return `null` if the ID doesn't exist. Line 24 (`currentUser.id === user.id`) will throw.
2. **No null check on `currentUser`** — If the `x-user-id` header is missing or the user doesn't exist, `currentUser.role` on line 24 throws.
3. **Auth via `x-user-id` header is trivially spoofable** — any client can set this header. Should use a session token/JWT, not a raw user ID.
4. **Leaks internal error details to client** — Line 31 returns `error.message` directly, which may expose DB schema, query details, or stack info.
