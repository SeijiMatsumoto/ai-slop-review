# 10 — LLM Streaming Endpoint (TypeScript/Vercel AI SDK)

**Categories:** Hallucinated APIs, Security, Missing guards

1. **`onToken` callback doesn't exist in Vercel AI SDK's `streamText`** — The actual callbacks are `onChunk`, `onStepFinish`, `onFinish`. `onToken` is hallucinated.
2. **`sendReasoning` is not a valid option on `toDataStreamResponse`** — This option doesn't exist in the Vercel AI SDK.
3. **User controls the `model` parameter** — The client can pass any model string (e.g., `"gpt-4-32k"`, `"o1-preview"`) and it's used directly, potentially incurring unexpected costs or accessing models the app shouldn't use.
4. **Error message leaks stack trace** — `getErrorMessage` returns `error.message` and `error.stack` to the client, exposing internal details.
5. **No auth on either endpoint** — No verification that the caller is authorized. Anyone can POST to generate completions or GET to read chat history.
6. **`console.log` on every token** — Logging every single token in a streaming response is extremely noisy and could be a performance issue in production.
7. **No input validation on `messages`** — The messages array from the client is passed directly to the LLM with no sanitization or size limits.
