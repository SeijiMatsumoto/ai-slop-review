# 13 — Prisma CRUD (TypeScript/Next.js)

**Categories:** Convention violation, SQL injection, Performance (N+1)

1. **Uses raw SQL everywhere instead of Prisma's query builder** — The whole point of having Prisma is to use its type-safe query builder. Every query uses `$queryRawUnsafe` with string interpolation, defeating the purpose entirely.
2. **SQL injection in every endpoint** — `tag`, `authorId`, `body.title`, `body.content`, `id`, and all update values are interpolated directly into SQL strings via template literals.
3. **N+1 query in GET** — Lines 30-38 fetch comments one-by-one for each post in a loop. Should be a single JOIN or Prisma `include`.
4. **Inconsistent naming conventions** — Response fields use PascalCase (`Data`, `Page`, `Limit`, `Success`) mixed with snake_case DB columns (`author_id`, `created_at`). This is neither standard JS (camelCase) nor consistent.
5. **Variable naming convention violations** — `PostsWithComments` (PascalCase for a local variable), `Updates`, `Key`, `Value` — all should be camelCase.
6. **No auth or ownership checks** — Anyone can update or delete any post.
7. **DELETE doesn't handle "not found"** — Silently succeeds even if the post doesn't exist.
8. **New `PrismaClient()` per file** — Should use a singleton pattern to avoid connection pool exhaustion.
