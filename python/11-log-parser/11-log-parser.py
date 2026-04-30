# Review this code — find bugs, understand the logic, complete the TODOs

from datetime import datetime
from collections import defaultdict


def parse_line(line: str) -> dict | None:
    try:
        timestamp_str = line[:18]
        rest = line[19:]

        parts = rest.split(" ", 2)
        if len(parts) < 3:
            return None

        level, service, message = parts[0], parts[1], parts[2]

        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        return {
            "timestamp": timestamp,
            "level": level,
            "service": service,
            "message": message.strip(),
        }
    except (ValueError, IndexError):
        return None


def parse_file(lines: list[str]) -> list[dict]:
    records: list[dict] = []
    for line in lines:
        record = parse_line(line.strip())
        if record is not None:
            records.append(record)
    return records


def group_by_hour(records: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        key = record["timestamp"].strftime("%Y-%m-%d %H:%M")
        groups[key].append(record)
    return dict(groups)


def error_rate_by_service(records: list[dict]) -> dict[str, float]:
    service_total: dict[str, int] = defaultdict(int)
    service_errors: dict[str, int] = defaultdict(int)

    for record in records:
        service = record["service"]
        service_total[service] += 1
        if record["level"] == "ERROR":
            service_errors[service] += 1

    return {
        service: service_errors[service] / total
        for service, total in service_total.items()
    }


def top_errors(records: list[dict], n: int) -> list[dict]:
    errors = [r for r in records if r["level"] == "ERROR"]
    errors_sorted = sorted(errors, key=lambda r: r["timestamp"], reverse=True)
    return errors_sorted[:n]


# TODO: Add a function that finds the peak hour (hour with most log entries) and returns
#       the hour string and count
# TODO: Add support for multi-line log entries where continuation lines start with
#       whitespace (they should be merged into the previous record's message)


if __name__ == "__main__":
    log_lines = [
        "2024-03-15 14:23:45 INFO  order_service Order received id=1001",
        "2024-03-15 14:23:46 DEBUG order_service Validating order id=1001",
        "2024-03-15 14:24:01 ERROR order_service Failed to submit order id=9821",
        "2024-03-15 14:24:05 INFO  risk_service  Risk check passed id=1001",
        "2024-03-15 14:24:10 ERROR risk_service  Position limit breached trader=T42",
        "2024-03-15 14:25:00 INFO  order_service Order filled id=1001",
        "2024-03-15 15:01:00 ERROR order_service Connection timeout to exchange",
        "2024-03-15 15:01:30 ERROR order_service Retry failed exchange=NYSE",
        "2024-03-15 15:02:00 INFO  order_service Reconnected to exchange",
        "2024-03-15 15:02:15 WARN  risk_service  Approaching daily limit trader=T42",
        "not a valid log line",
        "",
        "2024-03-15 16:00:00 INFO  order_service End of day summary",
    ]

    print("=== parse_line (individual) ===")
    sample = "2024-03-15 14:23:45 ERROR order_service Failed to submit order id=9821"
    result = parse_line(sample)
    print(f"  Result: {result}")

    print("\n=== parse_file ===")
    records = parse_file(log_lines)
    print(f"  Parsed {len(records)} records from {len(log_lines)} lines")
    for r in records[:3]:
        print(f"  {r}")

    print("\n=== group_by_hour ===")
    groups = group_by_hour(records)
    print(f"  Groups:")
    for key, group_records in groups.items():
        print(f"    {key}: {len(group_records)} records")

    print("\n=== error_rate_by_service ===")
    error_rates = error_rate_by_service(records)
    for service, rate in error_rates.items():
        print(f"  {service}: {rate:.1%} error rate")

    print("\n=== top_errors (n=3) ===")
    top = top_errors(records, 3)
    for r in top:
        print(f"  {r.get('timestamp')} [{r.get('service')}] {r.get('message')}")
