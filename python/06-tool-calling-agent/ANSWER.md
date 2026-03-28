# 12 — Tool-Calling Agent (Python)

**Categories:** Missing guards (infinite loop, unbounded memory)

1. **No max iteration guard** — The `while True` loop on line 56 runs until the model stops calling tools. If the model keeps calling tools indefinitely, this loops forever. Need a `max_iterations` counter.
2. **Unbounded message history** — Every tool call and response is appended to `self.messages` with no truncation. Over a long conversation, this will exceed the model's context window and/or consume unbounded memory.
3. **No confirmation for dangerous actions** — `send_email` is called automatically with no human-in-the-loop check. The agent could email anyone anything.
4. **No rate limiting or cost tracking** — Each loop iteration makes an API call. A runaway agent could rack up significant API costs.
5. **Tool argument parsing trusts LLM output** — `json.loads(tool_call.function.arguments)` on line 66 can throw if the model produces malformed JSON. This would crash the entire agent loop.
6. **Global mutable registry** — `tools_registry` is module-level and mutable. In a multi-tenant or concurrent scenario, tools could bleed between agent instances.
