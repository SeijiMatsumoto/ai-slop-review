# Answer: Cron Scheduler

## Bug 1: Timezone-Naive Date Comparison

The `matchesCron` method uses `date.getMinutes()`, `date.getHours()`, etc., which return local time values. If cron expressions are intended to be in UTC (as is standard for cron), jobs will fire at the wrong times depending on the server's timezone. A job scheduled for `0 9 * * *` (9 AM UTC) would fire at 9 AM local time instead.

**Fix:** Use UTC methods (`date.getUTCMinutes()`, `date.getUTCHours()`, etc.) or explicitly document and handle timezone configuration:

```typescript
matchesCron(date: Date, parsed: ParsedCron): boolean {
  return (
    parsed.minute.includes(date.getUTCMinutes()) &&
    parsed.hour.includes(date.getUTCHours()) &&
    // ...
  );
}
```

## Bug 2: DST Gap Causes Skipped or Double Execution

The scheduler doesn't account for daylight saving time transitions. During spring-forward (e.g., 2:00 AM jumps to 3:00 AM), a job scheduled at 2:30 AM will be skipped because that time never occurs. During fall-back (e.g., 2:00 AM repeats), a job at 2:30 AM could run twice because the same minute occurs twice.

**Fix:** Use UTC for all scheduling (avoids DST entirely), or implement DST-aware logic that detects transitions and adjusts accordingly. Libraries like `luxon` or `date-fns-tz` can help.

## Bug 3: `setInterval` Drift Over Time

The scheduler uses `setInterval(() => this.tick(), 60 * 1000)` to check for due jobs. `setInterval` does not guarantee exact timing — it drifts due to event loop delays, CPU load, and timer coalescing. Over hours, the tick can drift enough to miss a minute boundary entirely (e.g., tick at 10:00:59.999, then next tick at 10:02:00.001, skipping 10:01) or fire twice in the same minute.

**Fix:** Use `setTimeout` with dynamic delay calculation, aligning to the next minute boundary:

```typescript
private scheduleNextTick(): void {
  const now = Date.now();
  const nextMinute = Math.ceil(now / 60000) * 60000;
  const delay = nextMinute - now + 100; // small buffer
  setTimeout(() => {
    this.tick();
    this.scheduleNextTick();
  }, delay);
}
```

## Bug 4: No Distributed Lock

If the application is deployed across multiple server instances (common in production), each instance runs its own scheduler. Every job will execute once per instance — a daily report job runs 3 times if there are 3 servers. There's no distributed locking mechanism to ensure a job runs exactly once across the cluster.

**Fix:** Implement a distributed lock using Redis (e.g., Redlock), a database advisory lock, or a dedicated leader election mechanism:

```typescript
const lockKey = `cron:lock:${job.id}:${now.toISOString().slice(0, 16)}`;
const acquired = await redis.set(lockKey, instanceId, "NX", "EX", 300);
if (!acquired) return; // another instance already claimed this run
```

## Bug 5: Error in One Job Kills the Entire Tick

In the `tick()` method, jobs are iterated with `for...of` and each `await job.handler()` has no try/catch. If any job throws an error, the entire tick aborts — all subsequent jobs in that tick are skipped. One flaky job can prevent all other jobs from running.

**Fix:** Wrap each job execution in a try/catch:

```typescript
for (const [id, job] of this.jobs) {
  if (!job.enabled) continue;
  try {
    const parsed = this.parseCronExpression(job.expression);
    if (this.matchesCron(now, parsed)) {
      await job.handler();
      job.lastRun = now;
    }
  } catch (error) {
    console.error(`[Scheduler] Job "${job.name}" failed:`, error);
    this.emit("jobFailed", { job, error });
  }
}
```
