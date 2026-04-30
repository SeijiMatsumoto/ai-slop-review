# Review this code — find bugs, understand the logic, complete the TODOs

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Event:
    event_id: str
    user_id: str
    event_type: str
    timestamp: str   # ISO format: "2024-03-15T14:23:45"
    value: float     # e.g. revenue, duration in ms, item count


def group_by_day(events: list[Event]) -> dict[str, list[Event]]:
    groups: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        key = event.timestamp[:16]
        groups[key].append(event)
    return dict(groups)


def daily_summary(events: list[Event]) -> dict[str, dict]:
    groups = group_by_day(events)
    result: dict[str, dict] = {}

    for day, day_events in groups.items():
        values = [e.value for e in day_events]
        result[day] = {
            "count": len(day_events),
            "total": sum(values),
            "average": sum(values) / len(events),
            "unique_users": len({e.user_id for e in day_events}),
        }

    return result


def events_by_type(events: list[Event]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for event in events:
        counts[event.event_type] += 1
    return dict(counts)


def top_users(events: list[Event], n: int) -> list[tuple[str, float]]:
    totals: dict[str, float] = defaultdict(float)
    for event in events:
        totals[event.user_id] += event.value
    return sorted(totals.items(), key=lambda x: x[1], reverse=True)[:n]


# TODO: Add a period_over_period(events, current_start, current_end, prev_start, prev_end)
#       function comparing two date ranges; return {"current_total", "prev_total", "change_pct"}
#       Formula (given): change_pct = (current - prev) / prev * 100; return None if prev == 0
# TODO: Add a percentile(values: list[float], p: float) -> float | None function
#       Formula (given): sort ascending, index = int(len(values) * p / 100) clamped to
#       len(values) - 1; return None if list is empty


if __name__ == "__main__":
    events = [
        Event("E001", "user-1", "purchase",  "2024-03-15T09:30:00", 49.99),
        Event("E002", "user-2", "purchase",  "2024-03-15T11:00:00", 99.99),
        Event("E003", "user-1", "page_view", "2024-03-15T11:30:00", 1.0),
        Event("E004", "user-3", "purchase",  "2024-03-15T14:00:00", 149.99),
        Event("E005", "user-1", "purchase",  "2024-03-16T09:00:00", 29.99),
        Event("E006", "user-2", "page_view", "2024-03-16T10:00:00", 1.0),
        Event("E007", "user-4", "purchase",  "2024-03-16T15:00:00", 199.99),
        Event("E008", "user-1", "refund",    "2024-03-17T10:00:00", -49.99),
        Event("E009", "user-3", "purchase",  "2024-03-17T11:00:00", 79.99),
        Event("E010", "user-2", "purchase",  "2024-03-17T16:00:00", 59.99),
    ]

    print("=== group_by_day ===")
    groups = group_by_day(events)
    print(f"  Groups: {sorted(groups.keys())}")
    print(f"  Expected 3 groups (one per calendar day), got: {len(groups)}")

    print("\n=== daily_summary ===")
    summary = daily_summary(events)
    for day, data in sorted(summary.items()):
        print(f"  {day}: {data}")

    print("\n=== Spot-check average for 2024-03-15 ===")
    day15_values = [49.99, 99.99, 1.0, 149.99]
    expected_avg = sum(day15_values) / len(day15_values)
    print(f"  Expected average: {expected_avg:.4f}")

    print("\n=== events_by_type ===")
    for etype, count in sorted(events_by_type(events).items()):
        print(f"  {etype}: {count}")

    print("\n=== top_users (n=3) ===")
    for user, total in top_users(events, 3):
        print(f"  {user}: ${total:.2f}")
