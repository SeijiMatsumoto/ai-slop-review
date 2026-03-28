# 07 — useDebounce Hook (TypeScript/React)

**Categories:** Overcomplicated abstraction, Hallucinated API

1. **Massive over-engineering** — A `createDebouncerFactory` factory function that returns a `createDebouncer` function, with full `DebounceConfig` interface, for a simple debounce hook. This is ~100 lines for what `lodash.debounce` or 15 lines of custom code does.
2. **`useDebouncedValue` uses `useState` without importing it** — Line 106 references `useState` but only `useRef, useCallback, useMemo, useEffect` are imported. This will fail at runtime.
3. **`AbortController.abort({ reason: "cleanup" })` — incorrect API** — `abort()` takes an optional reason as a direct argument, not an object. Also, creating `AbortController` outside `useEffect` means a new one is created every render.
4. **`options` object in deps array causes infinite re-renders** — Line 99 `useMemo(..., [delay, options])` — the `options` object is recreated every render (referential inequality), so the `useMemo` recomputes every time.
5. **`useDebouncedValue` creates AbortController on every render** — Line 105 creates a new controller outside useEffect, which is wasteful and doesn't actually abort anything useful.
