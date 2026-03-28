# 03 — Dashboard Card (TSX/React)

**Categories:** Performance, Missing null guards

1. **`useEffect` missing `refreshInterval` in dependency array** — If `refreshInterval` changes, the interval is never updated. The effect captures the stale value.
2. **`onMetricClick` called without null check** — The prop is optional (`onMetricClick?`) but line 63 calls `onMetricClick(metric)` unconditionally. Crashes if not provided.
3. **`DashboardGrid` missing `key` prop** — Line 78 `<DashboardCard {...card} />` in a `.map()` has no `key`, causing React reconciliation warnings and potential bugs.
4. **Initializes state from `metrics` prop but then overwrites with API data** — `useState(metrics)` seeds local state, but the interval fetches from a generic `/api/metrics` endpoint that presumably returns *all* metrics, not the ones for this card. The prop-based data is immediately discarded.
5. **No error handling on fetch** — If `/api/metrics` fails, `response.json()` will throw. No loading or error state.
