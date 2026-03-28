# 04 — CSV Importer (Python/Flask)

**Categories:** Security (SQL injection)

1. **SQL injection in `import_users`** — f-string interpolation of `email`, `name`, `role`, `department` directly into SQL. A malicious CSV row like `name = "'; DROP TABLE users; --"` is catastrophic. Must use parameterized queries.
2. **SQL injection in `search_users`** — Same issue with `query` and `department` from query params interpolated into raw SQL.
3. **No authentication on either endpoint** — Anyone can bulk-import users or search the database.
4. **User-supplied `role` field from CSV** — An attacker can set `role` to `"admin"` in the CSV, creating admin accounts.
5. **Bare `except` catches everything silently** — Errors per row are caught generically, which could mask data corruption or injection-related errors.
