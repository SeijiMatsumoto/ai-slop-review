// AI-generated PR — review this code
// Description: Added task scheduler with cron expression support for recurring jobs

import { EventEmitter } from "events";

interface CronJob {
  id: string;
  name: string;
  expression: string;
  handler: () => Promise<void>;
  enabled: boolean;
  lastRun: Date | null;
  nextRun: Date | null;
}

interface ParsedCron {
  minute: number[];
  hour: number[];
  dayOfMonth: number[];
  month: number[];
  dayOfWeek: number[];
}

class CronScheduler extends EventEmitter {
  private jobs: Map<string, CronJob> = new Map();
  private intervalId: NodeJS.Timeout | null = null;
  private running = false;

  /**
   * Parse a cron expression into its component parts.
   * Supports: minute hour dayOfMonth month dayOfWeek
   */
  parseCronExpression(expression: string): ParsedCron {
    const parts = expression.trim().split(/\s+/);
    if (parts.length !== 5) {
      throw new Error(`Invalid cron expression: ${expression}`);
    }

    return {
      minute: this.parseField(parts[0], 0, 59),
      hour: this.parseField(parts[1], 0, 23),
      dayOfMonth: this.parseField(parts[2], 1, 31),
      month: this.parseField(parts[3], 1, 12),
      dayOfWeek: this.parseField(parts[4], 0, 6),
    };
  }

  private parseField(field: string, min: number, max: number): number[] {
    if (field === "*") {
      return Array.from({ length: max - min + 1 }, (_, i) => min + i);
    }

    const values: number[] = [];

    for (const part of field.split(",")) {
      if (part.includes("/")) {
        const [range, stepStr] = part.split("/");
        const step = parseInt(stepStr, 10);
        const start = range === "*" ? min : parseInt(range, 10);
        for (let i = start; i <= max; i += step) {
          values.push(i);
        }
      } else if (part.includes("-")) {
        const [startStr, endStr] = part.split("-");
        const start = parseInt(startStr, 10);
        const end = parseInt(endStr, 10);
        for (let i = start; i <= end; i++) {
          values.push(i);
        }
      } else {
        values.push(parseInt(part, 10));
      }
    }

    return values.filter((v) => v >= min && v <= max);
  }

  /**
   * Check if a given date matches a cron expression.
   */
  matchesCron(date: Date, parsed: ParsedCron): boolean {
    return (
      parsed.minute.includes(date.getMinutes()) &&
      parsed.hour.includes(date.getHours()) &&
      parsed.dayOfMonth.includes(date.getDate()) &&
      parsed.month.includes(date.getMonth() + 1) &&
      parsed.dayOfWeek.includes(date.getDay())
    );
  }

  /**
   * Register a new job with the scheduler.
   */
  addJob(
    id: string,
    name: string,
    expression: string,
    handler: () => Promise<void>
  ): CronJob {
    // Validate the expression
    this.parseCronExpression(expression);

    const job: CronJob = {
      id,
      name,
      expression,
      handler,
      enabled: true,
      lastRun: null,
      nextRun: null,
    };

    this.jobs.set(id, job);
    this.emit("jobAdded", job);
    console.log(`[Scheduler] Registered job "${name}" (${expression})`);
    return job;
  }

  /**
   * Remove a job from the scheduler.
   */
  removeJob(id: string): boolean {
    const job = this.jobs.get(id);
    if (job) {
      this.jobs.delete(id);
      this.emit("jobRemoved", job);
      console.log(`[Scheduler] Removed job "${job.name}"`);
      return true;
    }
    return false;
  }

  /**
   * Enable or disable a specific job.
   */
  setJobEnabled(id: string, enabled: boolean): void {
    const job = this.jobs.get(id);
    if (job) {
      job.enabled = enabled;
      console.log(
        `[Scheduler] Job "${job.name}" ${enabled ? "enabled" : "disabled"}`
      );
    }
  }

  /**
   * Start the scheduler — checks for due jobs every 60 seconds.
   */
  start(): void {
    if (this.running) {
      console.log("[Scheduler] Already running");
      return;
    }

    this.running = true;
    console.log("[Scheduler] Starting scheduler...");

    // Run an immediate check
    this.tick();

    // Check every 60 seconds for due jobs
    this.intervalId = setInterval(() => {
      this.tick();
    }, 60 * 1000);
  }

  /**
   * Stop the scheduler.
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.running = false;
    console.log("[Scheduler] Stopped");
  }

  /**
   * Execute a single tick — check all jobs and run any that are due.
   */
  private async tick(): Promise<void> {
    const now = new Date();
    console.log(`[Scheduler] Tick at ${now.toISOString()}`);

    for (const [id, job] of this.jobs) {
      if (!job.enabled) continue;

      const parsed = this.parseCronExpression(job.expression);

      if (this.matchesCron(now, parsed)) {
        console.log(`[Scheduler] Running job "${job.name}"...`);

        const startTime = Date.now();
        await job.handler();
        const duration = Date.now() - startTime;

        job.lastRun = now;
        this.emit("jobCompleted", { job, duration });
        console.log(
          `[Scheduler] Job "${job.name}" completed in ${duration}ms`
        );
      }
    }
  }

  /**
   * Get status of all registered jobs.
   */
  getStatus(): Array<{
    id: string;
    name: string;
    expression: string;
    enabled: boolean;
    lastRun: Date | null;
  }> {
    return Array.from(this.jobs.values()).map((job) => ({
      id: job.id,
      name: job.name,
      expression: job.expression,
      enabled: job.enabled,
      lastRun: job.lastRun,
    }));
  }
}

// Usage example
const scheduler = new CronScheduler();

scheduler.addJob("cleanup", "Database Cleanup", "0 2 * * *", async () => {
  // Runs at 2:00 AM every day
  console.log("Running database cleanup...");
  // await db.query("DELETE FROM sessions WHERE expired_at < NOW()");
});

scheduler.addJob("report", "Daily Report", "30 9 * * 1-5", async () => {
  // Runs at 9:30 AM on weekdays
  console.log("Generating daily report...");
  // await reportService.generateAndSend();
});

scheduler.addJob("heartbeat", "Health Check", "*/5 * * * *", async () => {
  // Runs every 5 minutes
  console.log("Sending heartbeat...");
  // await healthCheck.ping();
});

scheduler.start();

export { CronScheduler, CronJob };
