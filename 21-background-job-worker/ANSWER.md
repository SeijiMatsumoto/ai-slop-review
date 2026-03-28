# Background Job Worker — Bugs

## Bug 1: Silently Acks Failed Jobs (Data Loss)
**Location:** `process_order`, the `except Exception` block (lines ~97-103)

The task catches all exceptions and returns a `{"status": "failed", ...}` dict instead of re-raising. From Celery's perspective, the task completed successfully (it returned a value). This means Celery will **never retry** the task, and the failed order is silently lost. The correct approach is to let the exception propagate (or use `self.retry(exc=e)`) so Celery can retry according to the task's retry policy.

## Bug 2: No Dead Letter Queue
**Location:** `process_order` exception handler

When an order fails, it is only logged with `logger.error()`. There is no mechanism to persist the failure for later review — no dead letter queue, no failed-jobs table, no alerting system. The `retry_failed_orders` task queries orders with `status = 'failed'`, but the `process_order` task never updates the order status to `'failed'` in the database (due to Bug 1 silently returning). Failed orders simply vanish.

## Bug 3: Unbounded Memory from Accumulating Results
**Location:** `process_batch` function (lines ~108-124)

The `results` list accumulates every individual order result in memory. For a large nightly batch (e.g., hundreds of thousands of orders), this list grows without bound and can exhaust worker memory. The final return value also includes the full `results` list, which gets serialized back to the result backend. A better approach would be to stream/aggregate results or store them externally.

## Bug 4: Pickle Deserialization of Untrusted Input (RCE)
**Location:** `process_order`, line `order_data = pickle.loads(serialized_order)`

The task uses `pickle.loads()` to deserialize order data received from the message queue. Python's `pickle` module can execute arbitrary code during deserialization. If an attacker can push a crafted message onto the Redis broker, they achieve **remote code execution** on the worker. The Celery config also sets `task_serializer="pickle"` and `accept_content=["pickle", "json"]`, compounding the issue. JSON should be used instead.

## Bug 5: Database Connection Never Returned to Pool on Error
**Location:** `process_order`, the `try/except` block

The database connection `conn` is created inside the `try` block, but `conn.close()` is only called in the happy path (after successful fulfillment). If any exception occurs (inventory check fails, payment capture fails, etc.), the `except` block does **not** close the connection. Over time, this leaks database connections until the pool is exhausted and the worker can no longer process any orders. The fix is to use a `finally` block or a context manager to ensure the connection is always closed.
