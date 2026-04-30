# Python Problems — Answer Key

## 01 - order-processor

**Bug 1** (`calculate_subtotal`): missing `* item.quantity`
```python
# wrong
return sum(item.unit_price * (1 - item.discount_pct) for item in items)
# fix
return sum(item.unit_price * item.quantity * (1 - item.discount_pct) for item in items)
```

**Bug 2** (`calculate_total`): tax applied to `subtotal` instead of `after_discount`
```python
# wrong
tax = calculate_tax(subtotal, tax_rate)
# fix
tax = calculate_tax(after_discount, tax_rate)
```

**TODOs:**
- `apply_coupon(subtotal, coupon)`: if type=="flat", return max(0, subtotal - value); if type=="pct", return subtotal * (1 - value)
- `group_by_discount(items)`: `defaultdict(list)`, key = `item.discount_pct`

---

## 02 - inventory-tracker

**Bug 1** (`SKU.available` property): `stock + reserved` should be `stock - reserved`
```python
# wrong
return self.stock + self.reserved
# fix
return self.stock - self.reserved
```

**Bug 2** (`reserve`): checks `qty > sku.stock` instead of `qty > sku.available` — allows over-reservation
```python
# wrong
if qty > sku.stock:
# fix
if qty > sku.available:
```

**TODOs:**
- `low_stock_alerts(threshold)`: `[s.sku_id for s in self.skus.values() if s.available < threshold]`
- `batch_reserve(reservations)`: try all reserves; on any failure, release all that succeeded and return False

---

## 03 - session-manager

**Bug 1** (`is_valid`): comparison inverted — returns True when session IS expired
```python
# wrong
return session["expires_at"] < time.monotonic()
# fix
return session["expires_at"] > time.monotonic()
```

**Bug 2** (`logout`): deletes using `session["user_id"]` as the dict key instead of `session_id`
```python
# wrong
del self.sessions[session["user_id"]]
# fix
del self.sessions[session_id]
```

**TODOs:**
- `refresh(session_id, extend_by)`: check `is_valid`, then set `expires_at = now + (extend_by or ttl_seconds)`
- `max_sessions_per_user` in `create()`: call `active_sessions(user_id)`, if len >= limit delete the one with the oldest `created_at`

---

## 04 - job-scheduler

**Bug 1** (`schedule`): negating priority inverts the order — highest number becomes highest priority, but spec says lowest number = highest priority
```python
# wrong
heapq.heappush(self._queue, (-job.priority, job))
# fix
heapq.heappush(self._queue, (job.priority, job))
```

**Bug 2** (`run_due`): `>=` means future jobs go to `ready` and past jobs go to `deferred` — backwards
```python
# wrong
if job.run_at >= now:
    ready.append(...)
# fix
if job.run_at <= now:
    ready.append(...)
```

**TODOs:**
- `cancel(job_id)`: rebuild `_queue` as `[(p, j) for p, j in self._queue if j.job_id != job_id]`, then `heapq.heapify`
- `retry_failed(max_retries)`: add `attempts: int = 0` to Job; in retry, increment and re-schedule if `< max_retries`

---

## 05 - cache-manager

**Bug 1** (`_is_expired`): `<` should be `>` — as written, entries are considered "expired" immediately and "fresh" after TTL
```python
# wrong
return time.monotonic() - entry.created_at < self.ttl_seconds
# fix
return time.monotonic() - entry.created_at > self.ttl_seconds
```

**Bug 2** (`_evict_lru`): `max` evicts the most recently used; should be `min` to evict least recently used
```python
# wrong
lru_key = max(self._store, key=lambda k: self._store[k].last_accessed)
# fix
lru_key = min(self._store, key=lambda k: self._store[k].last_accessed)
```

**TODOs:**
- `get_or_set(key, factory_fn)`: `val = self.get(key); return val if val is not None else (self.set(key, factory_fn()) or self.get(key))`
  - Cleaner: compute, store, return
- `clear_expired()`: collect keys where `_is_expired(entry)`, delete them, return count

---

## 06 - notification-dispatcher

**Bug 1** (`_throttle_key`): key is `(user_id, channel)` — missing `message_type`, so different notification types on the same channel suppress each other
```python
# wrong
return (n.user_id, n.channel)
# fix
return (n.user_id, n.channel, n.message_type)
```

**Bug 2** (`_is_throttled`): `>` should be `<` — as written, it suppresses when enough time HAS passed (the opposite of throttling)
```python
# wrong
return time.time() - last > self.cooldown_seconds
# fix
return time.time() - last < self.cooldown_seconds
```

**TODOs:**
- `preferences` parameter: in `dispatch`, check `preferences.get(n.user_id, [])`, skip if `n.channel` not in that list
- `flush_suppressed()`: filter `_suppressed` where cooldown has expired, re-attempt, remove successes, return sent IDs

---

## 07 - webhook-dispatcher

**Bug** (`dispatch`): linear backoff instead of exponential (formula given in file header)
```python
# wrong
delay = event.base_delay * attempt
# fix
delay = event.base_delay * (2 ** attempt)
```

Note: attempt 0 still has delay=0 because of `if attempt > 0: time.sleep(delay)`. With fix:
- attempt 0: no sleep
- attempt 1: sleep(base * 2)
- attempt 2: sleep(base * 4)

**TODOs:**
- `dead_letter_retry()`: loop `dead_letter[:]`, call `dispatch(event)`, remove from `dead_letter` on success, return successful IDs
- `max_delay` cap: `delay = min(event.base_delay * (2 ** attempt), event.max_delay)`

---

## 08 - search-ranker

**Bug 1** (`search`): sort ascending instead of descending — lowest score returned first
```python
# wrong
scored.sort(key=lambda x: x[0])
# fix
scored.sort(key=lambda x: x[0], reverse=True)
```

**Bug 2** (`search`): pagination treats `page` as 0-indexed but callers use 1-indexed
```python
# wrong
start = page * page_size         # page=1 → start=10 (skips first 10)
# fix
start = (page - 1) * page_size  # page=1 → start=0
```

**TODOs:**
- `highlight(doc, query)`: replace each matched term in title/body with `<b>term</b>` using `str.replace`
- Tag boosting in `score_document`: `if term in doc.tags: score += boost` (e.g. 3.0)

---

## 09 - subscription-manager

**Bug** (`change_plan`): `sub.price` not updated after plan change — stays at old plan's price; `monthly_revenue()` will report stale amounts
```python
# missing line after sub.plan = new_plan:
sub.price = PLANS[new_plan]
```

**TODOs:**
- `trial_subscribe(user_id, plan, trial_days)`: set `status="trial"`, add `trial_ends_on_day = start_day + trial_days`; exclude from `monthly_revenue`
- `bulk_discount(user_ids, discount_pct)`: for each user_id in list, if active, `sub.price *= (1 - discount_pct)`

---

## 10 - report-builder

**Bug 1** (`group_by_day`): `timestamp[:16]` gives minute-level grouping ("2024-03-15T14:23"), should be `[:10]` for day-level ("2024-03-15")
```python
# wrong
key = event.timestamp[:16]
# fix
key = event.timestamp[:10]
```

**Bug 2** (`daily_summary`): average divides by `len(events)` (all events) instead of `len(values)` (events in this day)
```python
# wrong
"average": sum(values) / len(events),
# fix
"average": sum(values) / len(values),
```

**TODOs:**
- `period_over_period(events, current_start, current_end, prev_start, prev_end)`:
  filter by timestamp range, sum values, compute change_pct = (curr - prev) / prev * 100 (None if prev == 0)
- `percentile(values, p)`: sort, index = min(int(len(values) * p / 100), len(values) - 1), return values[index] or None if empty
