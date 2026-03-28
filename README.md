# AI Slop Code Review

A collection of 40 AI-generated code snippets for practicing code review skills. Each file contains intentional bugs, security vulnerabilities, or logic errors typical of AI-generated code ("AI slop").

## How to Use

1. Open a problem folder and review the code file as if it were a real pull request
2. Identify as many bugs, security issues, and logic errors as you can
3. Check your findings against the `ANSWER.md` in the same folder

## TypeScript Problems

| #  | Folder                        | Language       | Topics                          |
|----|-----------------------------|----------------|---------------------------------|
| 01 | `01-user-lookup-api/`       | TypeScript     | Null guards, Security           |
| 02 | `02-dashboard-card/`        | React/TSX      | Performance, Null guards        |
| 03 | `03-form-handler/`          | TypeScript     | Security, Mass assignment       |
| 04 | `04-use-debounce/`          | TypeScript     | Over-engineering, Hallucinated API |
| 05 | `05-rate-limiter/`          | TypeScript     | Logic errors, Security          |
| 06 | `06-llm-streaming/`         | TypeScript     | Hallucinated APIs, Security     |
| 07 | `07-prisma-crud/`           | TypeScript     | SQL injection, N+1 queries      |
| 08 | `08-multi-model-router/`    | TypeScript     | Key leakage, Prompt injection   |
| 09 | `09-webhook-verifier/`      | TypeScript     | Timing attacks, Replay attacks  |
| 10 | `10-redis-session-store/`   | TypeScript     | Race conditions, Session fixation |
| 11 | `11-retry-with-backoff/`    | TypeScript     | Idempotency, Thundering herd    |
| 12 | `12-oauth-callback/`        | TypeScript     | CSRF, Open redirect             |
| 13 | `13-search-autocomplete/`   | React/TSX      | Race conditions, XSS            |
| 14 | `14-websocket-chat/`        | TypeScript     | No auth, Memory leaks           |
| 15 | `15-cron-scheduler/`        | TypeScript     | Timezone bugs, DST, Drift       |
| 16 | `16-graphql-resolver/`      | TypeScript     | Query depth DoS, N+1            |
| 17 | `17-feature-flag-sdk/`      | TypeScript     | Stale closures, Non-deterministic rollout |
| 18 | `18-jwt-auth-middleware/`   | TypeScript     | Algorithm confusion, Timing attacks |
| 19 | `19-event-emitter-bus/`     | TypeScript     | Memory leaks, Error handling    |
| 20 | `20-markdown-parser/`       | TypeScript     | ReDoS, XSS, Edge cases          |

## Python Problems

| #  | Folder                        | Language       | Topics                          |
|----|-----------------------------|----------------|---------------------------------|
| 01 | `01-pagination-processor/`  | Python         | Off-by-one errors               |
| 02 | `02-csv-importer/`          | Python/Flask   | SQL injection                   |
| 03 | `03-async-api-client/`      | Python         | N+1 queries, Hardcoded secrets  |
| 04 | `04-data-pipeline/`         | Python         | Over-engineering                |
| 05 | `05-rag-retrieval/`         | Python         | Math errors, Silent failures    |
| 06 | `06-tool-calling-agent/`    | Python         | Infinite loops, Missing guards  |
| 07 | `07-llm-eval-scorer/`       | Python         | Float comparison, Silent failures |
| 08 | `08-file-upload-handler/`   | Python/FastAPI | Path traversal, File validation |
| 09 | `09-pagination-cursor/`     | Python/Django  | Cursor tampering, SQL injection |
| 10 | `10-background-job-worker/` | Python/Celery  | Silent data loss, Pickle RCE    |
| 11 | `11-env-config-loader/`     | Python         | eval() injection, Secret leaks  |
| 12 | `12-image-resize-service/`  | Python/FastAPI | Decompression bomb, EXIF leaks  |
| 13 | `13-password-reset/`        | Python/Flask   | Guessable tokens, User enumeration |
| 14 | `14-jwt-token-service/`     | Python         | Weak secrets, Token reuse, Expiration bugs |
| 15 | `15-database-migration-runner/` | Python     | SQL injection, No transactions, Ordering |
| 16 | `16-api-rate-limiter/`      | Python/Flask   | Race conditions, Bypass, Time bugs |
| 17 | `17-log-aggregator/`        | Python         | Regex injection, Memory, File handling |
| 18 | `18-cache-decorator/`       | Python         | Memory leaks, Thread safety     |
| 19 | `19-webhook-dispatcher/`    | Python         | SSRF, Retry logic, Secret leaks |
| 20 | `20-schema-validator/`      | Python         | Type coercion, Recursive depth, eval() |
