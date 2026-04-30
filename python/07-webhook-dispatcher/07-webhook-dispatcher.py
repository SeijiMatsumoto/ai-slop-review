# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Webhook: an HTTP POST your system sends to a URL when an event happens
#   Delivery attempt: one try to POST the webhook payload to the target URL
#   Retry: if a delivery fails, try again after a delay
#   Exponential backoff: delay doubles with each retry attempt
#     Formula (given): delay_seconds = base_delay * (2 ** attempt_number)
#                      attempt_number starts at 0; no delay before the first attempt
#   Dead letter: events that failed all retries — set aside for manual review

from dataclasses import dataclass, field
import time


@dataclass
class WebhookEvent:
    event_id: str
    url: str
    payload: dict
    max_retries: int = 3
    base_delay: float = 1.0


@dataclass
class DeliveryAttempt:
    event_id: str
    attempt: int
    success: bool
    error: str | None
    delay_before: float


class WebhookDispatcher:
    def __init__(self, sender=None) -> None:
        self._sender = sender or self._default_sender
        self.history: list[DeliveryAttempt] = []
        self.dead_letter: list[WebhookEvent] = []

    @staticmethod
    def _default_sender(url: str, payload: dict) -> bool:
        return True

    def dispatch(self, event: WebhookEvent) -> bool:
        for attempt in range(event.max_retries):
            delay = event.base_delay * attempt

            if attempt > 0:
                time.sleep(delay)

            try:
                success = self._sender(event.url, event.payload)
            except Exception:
                success = False

            self.history.append(DeliveryAttempt(
                event_id=event.event_id,
                attempt=attempt,
                success=success,
                error=None if success else "send failed",
                delay_before=delay,
            ))

            if success:
                return True

        self.dead_letter.append(event)
        return False

    def attempts_for(self, event_id: str) -> list[DeliveryAttempt]:
        return [a for a in self.history if a.event_id == event_id]

    def summary(self) -> dict:
        total = len({a.event_id for a in self.history})
        delivered = total - len(self.dead_letter)
        return {
            "total_events": total,
            "delivered": delivered,
            "failed": len(self.dead_letter),
            "total_attempts": len(self.history),
        }


# TODO: Add a dead_letter_retry() -> list[str] method that re-dispatches all events in
#       dead_letter with a fresh attempt count; remove from dead_letter on success;
#       return list of event_ids that were successfully delivered
# TODO: Add a max_delay: float parameter to WebhookEvent and cap the computed delay at
#       that value — so delays don't grow unbounded for events with many retries


if __name__ == "__main__":
    attempt_counts: dict[str, int] = {}

    def flaky_sender(url: str, payload: dict) -> bool:
        eid = payload.get("event_id", "?")
        attempt_counts[eid] = attempt_counts.get(eid, 0) + 1
        return attempt_counts[eid] >= 3   # succeeds on 3rd attempt

    dispatcher = WebhookDispatcher(sender=flaky_sender)

    events = [
        WebhookEvent("E001", "https://example.com/hooks", {"event_id": "E001", "type": "order.created"}, max_retries=3, base_delay=0.01),
        WebhookEvent("E002", "https://example.com/hooks", {"event_id": "E002", "type": "order.shipped"},  max_retries=2, base_delay=0.01),
        WebhookEvent("E003", "https://example.com/hooks", {"event_id": "E003", "type": "payment.failed"}, max_retries=3, base_delay=0.01),
    ]

    print("=== Dispatch events ===")
    for event in events:
        result = dispatcher.dispatch(event)
        print(f"  {event.event_id}: {'delivered' if result else 'FAILED → dead letter'}")

    print("\n=== Delivery attempts per event ===")
    for event in events:
        attempts = dispatcher.attempts_for(event.event_id)
        for a in attempts:
            print(f"  {a.event_id} attempt {a.attempt}: success={a.success}, delay_before={a.delay_before:.4f}s")

    print("\n=== Expected backoff delays (base=0.01s, exponential) ===")
    print("  attempt 0: 0.0000s (no delay before first try)")
    print("  attempt 1: 0.0100s  (0.01 * 2^1)")
    print("  attempt 2: 0.0400s  (0.01 * 2^2)")

    print("\n=== Summary ===")
    print(f"  {dispatcher.summary()}")
    print(f"  Dead letter: {[e.event_id for e in dispatcher.dead_letter]}")
