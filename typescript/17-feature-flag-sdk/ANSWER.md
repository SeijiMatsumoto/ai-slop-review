# Answer: Feature Flag SDK

## Bug 1: Evaluates Flags Synchronously Blocking Render

The `getFlag()` method, when the SDK is not yet initialized, synchronously reads and parses `localStorage.getItem("feature_flags")` and `JSON.parse()` on every call. While localStorage is synchronous by nature, this is called on every render cycle. More critically, the constructor kicks off an async `refreshFlags()` but provides no way to await it, meaning the first render always falls through to the synchronous localStorage path. Parsing a large JSON blob from localStorage on every render blocks the main UI thread.

**Fix:** Initialize the SDK asynchronously and provide an `isReady` promise. Use memoized/cached parsed values instead of re-parsing localStorage on every call:

```typescript
async initialize(): Promise<void> {
  this.loadFromCache();
  await this.refreshFlags();
}
```

## Bug 2: Stale Closure Captures Old Flags (React Hook)

The `useFeatureFlag` hook captures `sdk.getFlag(key, defaultValue)` once and assigns it. The `setEnabled` function is a no-op (`(_: boolean) => {}`). Even though `refreshFlags()` runs every 30 seconds in the interval, the returned `enabled` value never updates because:
1. `setEnabled` does nothing
2. There's no React state (`useState`) or effect (`useEffect`) to trigger a re-render
3. The component receives the stale value from the initial call forever

**Fix:** Use proper React hooks:

```typescript
function useFeatureFlag(sdk: FeatureFlagSDK, key: string, defaultValue = false) {
  const [enabled, setEnabled] = React.useState(() => sdk.getFlag(key, defaultValue));

  React.useEffect(() => {
    const interval = setInterval(async () => {
      await sdk.refreshFlags();
      setEnabled(sdk.getFlag(key, defaultValue));
    }, 30_000);
    return () => clearInterval(interval);
  }, [sdk, key, defaultValue]);

  return enabled;
}
```

## Bug 3: localStorage as Source of Truth

The SDK reads flags from `localStorage` first and only fetches from the server as a background refresh. Since localStorage is fully accessible to users via browser DevTools, anyone can open the console and run:

```javascript
const flags = JSON.parse(localStorage.getItem("feature_flags"));
flags.flags["premium_features"].enabled = true;
localStorage.setItem("feature_flags", JSON.stringify(flags));
```

This lets users enable premium features, bypass A/B tests, or toggle any flag locally. The client SDK should never be the authority on flag state.

**Fix:** Always use server-fetched values as the source of truth. Use localStorage only as a temporary fallback for the initial render, and overwrite it as soon as the server responds. For security-critical flags (e.g., premium access), enforce them server-side, not client-side.

## Bug 4: Percentage Rollout Uses `Math.random()`

In `getFlag()`, percentage rollouts use `Math.random() * 100` for each evaluation. This means the same user can get different results on every page load or even every render. A user with a 50% rollout flag sees the feature appear and disappear randomly, creating an inconsistent and broken experience.

**Fix:** Use a deterministic hash based on the user ID and flag key:

```typescript
private hashUserFlag(userId: string, flagKey: string): number {
  const str = `${userId}:${flagKey}`;
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash) % 100;
}

// In getFlag:
if (flag.rolloutPercentage < 100) {
  const bucket = this.hashUserFlag(this.config.userId!, key);
  return bucket < flag.rolloutPercentage;
}
```

## Bug 5: No Error Handling on Fetch

The `refreshFlags()` method has no try/catch around the `fetch()` call or the `response.json()` parse. If the flag service is down, returns a non-200 status, or returns malformed JSON, the SDK throws an unhandled error. Since `refreshFlags()` is called in the constructor, a single network failure during initialization crashes the entire application.

**Fix:** Wrap the fetch in try/catch and fall back gracefully:

```typescript
async refreshFlags(): Promise<void> {
  try {
    const response = await fetch(`${this.config.apiUrl}/flags`, { ... });
    if (!response.ok) {
      console.warn(`Flag service returned ${response.status}`);
      return;
    }
    const data = await response.json();
    // ... process flags ...
  } catch (error) {
    console.warn("Failed to fetch feature flags, using cached values:", error);
    // Keep existing flags as-is; don't clear them
  }
}
```
