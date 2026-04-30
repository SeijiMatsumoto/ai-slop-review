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
        self.failed: dict[str, tuple[Job, int]] = {}

    def schedule(self, job: Job) -> None:
        heapq.heappush(self._queue, (job.priority, job))

    def run_due(self) -> list[str]:
        now = time.time()
        ran: list[str] = []
        ready = []
        deferred = []

        while self._queue:
            pri, job = heapq.heappop(self._queue)
            if job.run_at <= now:
                ready.append((pri, job))
            else:
                deferred.append((pri, job))

        for pri, job in deferred:
            heapq.heappush(self._queue, (pri, job))

        for _, job in sorted(ready, key=lambda x: x[0]):
            job.status = "running"
            job_id = job.job_id
            try:
                self.results[job_id] = job.fn(*job.args)
                job.status = "done"
                ran.append(job_id)
            except Exception:
                job.status = "failed"
                self.failed[job_id] = (job, self.failed.get(job_id)[1] + 1 if job_id in self.failed else 0)

        return ran

    def pending_count(self) -> int:
        return len(self._queue)

    def queue_snapshot(self) -> list[dict]:
        return [
            {"job_id": job.job_id, "name": job.name, "priority": job.priority, "run_at": job.run_at}
            for _, job in sorted(self._queue)
        ]

    def cancel(self, job_id: str) -> bool:
        jobs = self._queue
        filtered_jobs = [(priority, job) for priority, job in jobs if job.job_id != job_id]
        if len(filtered_jobs) == len(jobs):
            return False

        self._queue = filtered_jobs
        heapq.heapify(self._queue)

        return True

    def retry_failed(self, max_retries: int):
        for job_id, job_tuple in self.failed.items():
            job = job_tuple[0]
            retries = job_tuple[1]
            if retries >= max_retries:
                continue

            job.run_at = time.time()
            self.failed[job_id] = (job, retries)
            self.schedule(job)

        return

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
    print(f"  Failed: {list(scheduler.failed.keys())}")
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

    print("\n=== cancel ===")
    s3 = JobScheduler()
    s3.schedule(Job("C001", "cancel-me",    run_at=now + 60, priority=2, fn=lambda: "should not run"))
    s3.schedule(Job("C002", "keep-me",      run_at=now + 60, priority=1, fn=lambda: "also not run yet"))
    print(f"  Queue before cancel: {s3.pending_count()} (expected 2)")
    result = s3.cancel("C001")
    print(f"  cancel('C001'): {result} (expected True)")
    print(f"  Queue after cancel: {s3.pending_count()} (expected 1)")
    print(f"  Remaining job: {s3.queue_snapshot()[0]['job_id']} (expected C002)")
    result2 = s3.cancel("nonexistent")
    print(f"  cancel('nonexistent'): {result2} (expected False)")

    print("\n=== retry_failed ===")
    s4 = JobScheduler()
    s4.schedule(Job("F001", "will-fail",    run_at=now - 1, priority=1, fn=lambda: 1 / 0))
    s4.schedule(Job("F002", "will-succeed", run_at=now - 1, priority=2, fn=lambda: "ok"))
    s4.run_due()
    print(f"  Failed jobs: {list(s4.failed.keys())} (expected ['F001'])")
    print(f"  Pending before retry: {s4.pending_count()} (expected 0)")
    s4.retry_failed(max_retries=2)
    print(f"  Pending after retry_failed(2): {s4.pending_count()} (expected 1 — F001 re-queued)")
    ran3 = s4.run_due()
    print(f"  Ran after retry: {ran3} (expected [] — F001 fails again)")
    print(f"  Failed list after 2nd run: {list(s4.failed.keys())}")
    s4.retry_failed(max_retries=2)
    print(f"  Pending after 2nd retry_failed(2): {s4.pending_count()} (expected 1 — F001 re-queued, still under limit)")
    s4.run_due()
    s4.retry_failed(max_retries=2)
    print(f"  Pending after 3rd retry_failed(2): {s4.pending_count()} (expected 0 — max_retries reached)")
