# Review this code — find bugs, understand the logic, complete the TODOs

from dataclasses import dataclass


@dataclass
class Event:
    event_id: str
    event_type: str
    source: str
    timestamp: int
    payload: dict


class Deduplicator:
    def __init__(self, window_seconds: int) -> None:
        self.window_seconds = window_seconds
        self.seen: dict[str, int] = {}

    def deduplicate(self, event: Event) -> bool:
        dedup_key = f"{event.source}:{event.event_type}"

        if dedup_key in self.seen:
            first_seen_time = self.seen[dedup_key]
            if event.timestamp - first_seen_time < self.window_seconds:
                return False  # duplicate

        self.seen[dedup_key] = event.timestamp
        return True  # not a duplicate

    def process_batch(self, events: list[Event]) -> list[Event]:
        return [event for event in events if self.deduplicate(event)]

    def purge_expired(self, current_time: int) -> None:
        keys_to_delete = [
            key for key, timestamp in self.seen.items()
            if current_time - timestamp > self.window_seconds
        ]
        for key in keys_to_delete:
            del self.seen[key]

    def stats(self) -> dict:
        return {
            "total_seen": len(self.seen),
            "unique_count": len(self.seen),
        }


# TODO: Add a per-event-type deduplication window (different event types can have
#       different TTLs instead of a single window_seconds for all)
# TODO: Add an audit_log that records every duplicate event that was suppressed, with
#       the reason (which original event it duplicated)


if __name__ == "__main__":
    dedup = Deduplicator(window_seconds=60)

    events = [
        Event("evt-001", "order_placed",  "trading-system", timestamp=1000, payload={"order_id": "O1"}),
        Event("evt-002", "order_placed",  "trading-system", timestamp=1010, payload={"order_id": "O2"}),
        # Same event_id — true duplicate
        Event("evt-001", "order_placed",  "trading-system", timestamp=1020, payload={"order_id": "O1"}),
        # Different event_id, same source+type
        Event("evt-003", "order_placed",  "trading-system", timestamp=1030, payload={"order_id": "O3"}),
        # Different source — should be independent
        Event("evt-004", "order_placed",  "risk-system",    timestamp=1040, payload={"order_id": "O4"}),
        # Different event type
        Event("evt-005", "order_filled",  "trading-system", timestamp=1050, payload={"order_id": "O1"}),
        # After window expires
        Event("evt-006", "order_placed",  "trading-system", timestamp=1100, payload={"order_id": "O6"}),
    ]

    print("=== deduplicate (one by one) ===")
    dedup2 = Deduplicator(window_seconds=60)
    for event in events:
        result = dedup2.deduplicate(event)
        status = "PASS" if result else "DUP "
        print(f"  {status} {event.event_id} {event.event_type} from {event.source} @ t={event.timestamp}")

    print("\n=== process_batch ===")
    dedup3 = Deduplicator(window_seconds=60)
    passed = dedup3.process_batch(events)
    print(f"  {len(passed)} of {len(events)} events passed deduplication")
    for e in passed:
        print(f"    {e.event_id} {e.event_type}")

    print("\n=== purge_expired ===")
    dedup4 = Deduplicator(window_seconds=60)
    dedup4.process_batch(events)
    print(f"  seen keys before purge: {len(dedup4.seen)}")

    # Purge at current_time = 1060 (60s after first event at 1000)
    dedup4.purge_expired(current_time=1060)
    print(f"  seen keys after purge at t=1060: {len(dedup4.seen)}")

    dedup4.purge_expired(current_time=1061)
    print(f"  seen keys after purge at t=1061: {len(dedup4.seen)}")

    print("\n=== stats ===")
    print(f"  {dedup4.stats()}")
