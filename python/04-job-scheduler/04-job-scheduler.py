# Review this code — find bugs, understand the logic, complete the TODOs

import heapq
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Job:
    job_id: str
    name: str
    run_at: float        # unix timestamp — when this job should run
    priority: int        # lower number = higher priority (1 is most urgent)
    fn: Callable
    args: tuple = field(default_factory=tuple)
    status: str = "pending"

    def __lt__(self, other: "Job") -> bool:
        return self.priority < other.priority


class JobScheduler:
    def __init__(self) -> None:
        self._queue: list[tuple[int, Job]] = []
        self.results: dict[str, object] = {}
        self.failed: list[Job] = []

    def schedule(self, job: Job) -> None:
        heapq.heappush(self._queue, (-job.priority, job))

    def run_due(self) -> list[str]:
        now = time.time()
        ran: list[str] = []
        ready = []
        deferred = []

        while self._queue:
            pri, job = heapq.heappop(self._queue)
            if job.run_at >= now:
                ready.append((pri, job))
            else:
                deferred.append((pri, job))

        for pri, job in deferred:
            heapq.heappush(self._queue, (pri, job))

        for _, job in sorted(ready, key=lambda x: x[0]):
            job.status = "running"
            try:
                self.results[job.job_id] = job.fn(*job.args)
                job.status = "done"
                ran.append(job.job_id)
            except Exception:
                job.status = "failed"
                self.failed.append(job)

        return ran

    def pending_count(self) -> int:
        return len(self._queue)

    def queue_snapshot(self) -> list[dict]:
        return [
            {"job_id": job.job_id, "name": job.name, "priority": job.priority, "run_at": job.run_at}
            for _, job in sorted(self._queue)
        ]


# TODO: Add a cancel(job_id: str) -> bool method that removes a pending job from the
#       queue before it runs (rebuild the heap without that job)
# TODO: Add a retry_failed(max_retries: int) method that re-schedules each failed job
#       up to max_retries times, tracking attempt count per job


if __name__ == "__main__":
    scheduler = JobScheduler()
    now = time.time()

    jobs = [
        Job("J001", "send-email",    run_at=now - 5,  priority=2, fn=lambda: "email sent"),
        Job("J002", "resize-image",  run_at=now - 2,  priority=3, fn=lambda: "image resized"),
        Job("J003", "sync-database", run_at=now - 10, priority=1, fn=lambda: "db synced"),
        Job("J004", "future-task",   run_at=now + 60, priority=1, fn=lambda: "should not run"),
        Job("J005", "failing-task",  run_at=now - 1,  priority=2, fn=lambda: 1 / 0),
    ]

    print("=== Schedule jobs ===")
    for job in jobs:
        scheduler.schedule(job)
        print(f"  Scheduled {job.job_id} ({job.name}) priority={job.priority}")

    print(f"\n  Queue size: {scheduler.pending_count()}")

    print("\n=== run_due ===")
    ran = scheduler.run_due()
    print(f"  Ran: {ran}")
    print(f"  Failed: {[j.job_id for j in scheduler.failed]}")
    print(f"  Still pending: {scheduler.pending_count()} (J004 should remain)")

    print("\n=== Results ===")
    for job_id, result in scheduler.results.items():
        print(f"  {job_id}: {result}")

    print("\n=== Priority ordering (independent check) ===")
    s2 = JobScheduler()
    for p in [3, 1, 2]:
        s2.schedule(Job(f"P{p}", f"task-pri-{p}", run_at=now - 1, priority=p, fn=lambda p=p: p))
    ran2 = s2.run_due()
    print(f"  Run order: {ran2} (expected: P1 first, then P2, then P3)")
    print(f"  Results: {s2.results}")
