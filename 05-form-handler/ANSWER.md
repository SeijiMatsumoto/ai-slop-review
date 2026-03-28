# 05 — Form Handler (TypeScript/Next.js Server Action)

**Categories:** Security (privilege escalation, logging secrets, mass assignment)

1. **Privilege escalation via `role` field** — The client submits the `role` directly from the form. Any user can register as `"admin"` by modifying the form data.
2. **Password logged in plaintext** — Line 26 logs the entire `data` object including `password` via `JSON.stringify`.
3. **Password stored in plaintext** — Line 37 saves `data.password` directly to the DB with no hashing.
4. **Mass assignment in `updateUserProfile`** — Lines 46-48 blindly spread all form fields into a Prisma update. A user could add `role=admin` or `email=someone@else.com` to the form data.
5. **No input validation** — No email format check, no password strength requirements, no name length limits.
6. **User ID leaked in redirect URL** — Line 42 puts `userId` in the query string, potentially exposable.
