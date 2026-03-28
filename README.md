# AI Slop Code Review

A collection of 30 AI-generated code snippets for practicing code review skills. Each file contains intentional bugs, security vulnerabilities, or logic errors typical of AI-generated code ("AI slop").

## How to Use

1. Open a problem folder and review the code file as if it were a real pull request
2. Identify as many bugs, security issues, and logic errors as you can
3. Check your findings against the `ANSWER.md` in the same folder

## Problems

| #  | Folder                        | Language       | Topics                          |
|----|-----------------------------|----------------|---------------------------------|
| 01 | `01-user-lookup-api/`       | TypeScript     | Null guards, Security           |
| 02 | `02-pagination-processor/`  | Python         | Off-by-one errors               |
| 03 | `03-dashboard-card/`        | React/TSX      | Performance, Null guards        |
| 04 | `04-csv-importer/`          | Python/Flask   | SQL injection                   |
| 05 | `05-form-handler/`          | TypeScript     | Security, Mass assignment       |
| 06 | `06-async-api-client/`      | Python         | N+1 queries, Hardcoded secrets  |
| 07 | `07-use-debounce/`          | TypeScript     | Over-engineering, Hallucinated API |
| 08 | `08-rate-limiter/`          | TypeScript     | Logic errors, Security          |
| 09 | `09-data-pipeline/`         | Python         | Over-engineering                |
| 10 | `10-llm-streaming/`         | TypeScript     | Hallucinated APIs, Security     |
| 11 | `11-rag-retrieval/`         | Python         | Math errors, Silent failures    |
| 12 | `12-tool-calling-agent/`    | Python         | Infinite loops, Missing guards  |
| 13 | `13-prisma-crud/`           | TypeScript     | SQL injection, N+1 queries      |
| 14 | `14-llm-eval-scorer/`       | Python         | Float comparison, Silent failures |
| 15 | `15-multi-model-router/`    | TypeScript     | Key leakage, Prompt injection   |
| 16 | `16-webhook-verifier/`      | TypeScript     | Timing attacks, Replay attacks  |
| 17 | `17-file-upload-handler/`   | Python/FastAPI | Path traversal, File validation |
| 18 | `18-redis-session-store/`   | TypeScript     | Race conditions, Session fixation |
| 19 | `19-pagination-cursor/`     | Python/Django  | Cursor tampering, SQL injection |
| 20 | `20-retry-with-backoff/`    | TypeScript     | Idempotency, Thundering herd    |
| 21 | `21-background-job-worker/` | Python/Celery  | Silent data loss, Pickle RCE    |
| 22 | `22-oauth-callback/`        | TypeScript     | CSRF, Open redirect             |
| 23 | `23-search-autocomplete/`   | React/TSX      | Race conditions, XSS            |
| 24 | `24-env-config-loader/`     | Python         | eval() injection, Secret leaks  |
| 25 | `25-websocket-chat/`        | TypeScript     | No auth, Memory leaks           |
| 26 | `26-image-resize-service/`  | Python/FastAPI | Decompression bomb, EXIF leaks  |
| 27 | `27-cron-scheduler/`        | TypeScript     | Timezone bugs, DST, Drift       |
| 28 | `28-graphql-resolver/`      | TypeScript     | Query depth DoS, N+1            |
| 29 | `29-password-reset/`        | Python/Flask   | Guessable tokens, User enumeration |
| 30 | `30-feature-flag-sdk/`      | TypeScript     | Stale closures, Non-deterministic rollout |
