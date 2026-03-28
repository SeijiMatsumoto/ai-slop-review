# AI Slop Code Review

A collection of 15 AI-generated code snippets for practicing code review skills. Each file contains intentional bugs, security vulnerabilities, or logic errors typical of AI-generated code ("AI slop").

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
