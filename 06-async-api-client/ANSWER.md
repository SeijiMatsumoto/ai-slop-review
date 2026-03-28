# 06 — Async API Client (Python)

**Categories:** Performance (N+1), Security (hardcoded secret)

1. **N+1 HTTP calls** — `enrich_orders` sequentially `await`s one API call per item across all orders. With 100 orders of 5 items each = 500 sequential HTTP requests. Should use `asyncio.gather` or batch endpoint.
2. **Hardcoded API key in source code** — Line 10 has `API_KEY = "sk_prod_..."` committed directly. Should use environment variables.
3. **aiohttp session never closed** — The `ClientSession` is created but never `.close()`d. Resource leak. Should use `async with` or implement `__aenter__`/`__aexit__`.
4. **Mutates original items** — Lines 35-37 modify `item` in-place (adding `product_name`, etc.) even though `order_copy` was supposed to be a copy. The `items` list inside the original `order` dict is shared.
5. **No error handling on HTTP calls** — If the catalog API returns a 404 or 500, `resp.json()` may throw or return unexpected structure. No retry logic.
6. **Deprecated `get_event_loop()`** — Line 39 uses `asyncio.get_event_loop()` which is deprecated in Python 3.10+ when no loop is running.
