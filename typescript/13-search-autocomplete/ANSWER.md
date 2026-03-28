# Search Autocomplete — Bugs

## Bug 1: Race Condition — Stale Results Overwrite Fresh
**Location:** The `useEffect` that calls `fetchResults()` (lines ~55-83)

Each time `debouncedQuery` changes, a new fetch fires. However, there is no mechanism to ignore responses from previous queries. If the user types "ab" and then "abc", the request for "ab" might resolve *after* the request for "abc" (due to network timing). When that happens, the results for "ab" overwrite the correct results for "abc". The `AbortController` is created but never used in cleanup (see Bug 3), so old requests are not cancelled. The fix is to either abort previous requests or track a request ID and ignore stale responses.

## Bug 2: XSS via `dangerouslySetInnerHTML`
**Location:** `dangerouslySetInnerHTML={{ __html: result.highlightedTitle }}` (line ~166)

The `highlightedTitle` field from the API response is rendered as raw HTML. If the API returns unsanitized content (or if an attacker can influence search results), arbitrary JavaScript can execute in the user's browser. For example, a result title of `<img src=x onerror=alert(document.cookie)>` would execute. The fix is to either sanitize the HTML (e.g., with DOMPurify) or implement highlighting on the client side using safe string operations.

## Bug 3: Creates AbortController But Never Actually Aborts
**Location:** The `useEffect` cleanup function (line ~82-84)

An `AbortController` is created at the top of the effect and its signal is passed to `fetch`. However, the cleanup function returned by the effect is empty — it's just `return () => { // cleanup }`. It should call `abortController.abort()` to cancel in-flight requests when the query changes or the component unmounts. Without this, the controller is useless and the race condition from Bug 1 persists.

## Bug 4: Fetches on Empty Query
**Location:** The `useEffect` with `fetchResults()` (lines ~55-83)

There is no guard checking whether `debouncedQuery` is empty before making the API call. When the user clears the input (or on initial mount when `query` is `""`), it will still fetch `${apiEndpoint}?q=` which may return all results or cause an unnecessary server load. The fix is to add a check like `if (!debouncedQuery.trim()) { setResults([]); setIsOpen(false); return; }` at the start of the effect.

## Bug 5: Dropdown Never Closes on Outside Click
**Location:** The entire component — missing click-outside handler

There is no event listener for clicks outside the autocomplete component. Once the dropdown opens (when results are available), it only closes if the user presses Escape, selects a result, or the results become empty. Clicking elsewhere on the page leaves the dropdown open, which is a poor UX. The fix is to add a `useEffect` that listens for `mousedown` events on `document` and checks if the click target is outside the component's container, closing the dropdown if so.
