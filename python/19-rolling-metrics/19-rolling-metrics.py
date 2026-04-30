# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Rolling window: only include data points in [reference_time - window_seconds, reference_time)
#   EMA (Exponential Moving Average): weighted average where recent points count more
#     Formula: EMA_t = alpha * value_t + (1 - alpha) * EMA_(t-1);  alpha in (0, 1)
#   Percentile: p95 means 95% of values fall below this value (useful for latency/risk)
#   Z-score: (value - mean) / std_dev — how many standard deviations from the mean a point is

from dataclasses import dataclass


@dataclass
class DataPoint:
    timestamp: int
    value: float


def rolling_window(
    points: list[DataPoint],
    window_seconds: int,
    reference_time: int,
) -> list[DataPoint]:
    return [
        p for p in points
        if p.timestamp >= reference_time - window_seconds and p.timestamp < reference_time
    ]


def rolling_average(
    points: list[DataPoint],
    window_seconds: int,
    reference_time: int,
) -> float | None:
    window = rolling_window(points, window_seconds, reference_time)
    if not window:
        return None
    return sum(p.value for p in window) / len(window)


def rolling_max(
    points: list[DataPoint],
    window_seconds: int,
    reference_time: int,
) -> float | None:
    window = rolling_window(points, window_seconds, reference_time)
    if not window:
        return None
    return max(p.value for p in window)


def rolling_min(
    points: list[DataPoint],
    window_seconds: int,
    reference_time: int,
) -> float | None:
    window = rolling_window(points, window_seconds, reference_time)
    if not window:
        return None
    return min(p.value for p in window)


def percentile(points: list[DataPoint], p: float) -> float | None:
    if not points:
        return None
    values = sorted(pt.value for pt in points)
    index = int(len(values) * p / 100)
    return values[index]


def compute_stats(
    points: list[DataPoint],
    window_seconds: int,
    reference_time: int,
) -> dict:
    window = rolling_window(points, window_seconds, reference_time)

    if not window:
        return {
            "count": 0,
            "mean": None,
            "min": None,
            "max": None,
            "p50": None,
            "p95": None,
            "p99": None,
        }

    values_sum = sum(p.value for p in window)
    mean = values_sum / len(window)

    return {
        "count": len(window),
        "mean": mean,
        "min": min(p.value for p in window),
        "max": max(p.value for p in window),
        "p50": percentile(window, 50),
        "p95": percentile(window, 95),
        "p99": percentile(window, 99),
    }


# TODO: Add an exponential moving average (EMA) function with a configurable
#       smoothing factor alpha (0 < alpha < 1)
# TODO: Add a detect_anomalies(points, window_seconds, reference_time, z_threshold)
#       function that flags points more than z_threshold standard deviations from
#       the rolling mean


if __name__ == "__main__":
    import random
    random.seed(42)

    base_time = 10000
    points: list[DataPoint] = []

    for i in range(100):
        ts = base_time - 900 + i * 10
        val = 100.0 + random.gauss(0, 10)
        points.append(DataPoint(timestamp=ts, value=val))

    # Add the point exactly at reference_time
    points.append(DataPoint(timestamp=base_time, value=200.0))

    reference_time = base_time
    window_seconds = 300

    print("=== rolling_window ===")
    window = rolling_window(points, window_seconds, reference_time)
    print(f"  Points in window: {len(window)}")
    print(f"  Most recent point at t={reference_time}: {'included' if any(p.timestamp == reference_time for p in window) else 'excluded'}")

    print("\n=== rolling_average ===")
    avg = rolling_average(points, window_seconds, reference_time)
    print(f"  Rolling average (300s): {avg:.4f}" if avg else "  None")

    print("\n=== rolling_max / rolling_min ===")
    rmax = rolling_max(points, window_seconds, reference_time)
    rmin = rolling_min(points, window_seconds, reference_time)
    print(f"  Max: {rmax:.4f}" if rmax else "  None")
    print(f"  Min: {rmin:.4f}" if rmin else "  None")

    print("\n=== percentile ===")
    try:
        p100 = percentile(window, 100)
        print(f"  p100: {p100}")
    except IndexError as e:
        print(f"  p100: IndexError — {e}")

    for p in [50, 95, 99]:
        val = percentile(window, p)
        print(f"  p{p}: {val:.4f}" if val is not None else f"  p{p}: None")

    print("\n=== compute_stats ===")
    stats = compute_stats(points, window_seconds, reference_time)
    for k, v in stats.items():
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
