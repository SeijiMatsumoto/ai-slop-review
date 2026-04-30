# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Threshold: a limit value that triggers an alert when breached
#   Consecutive: N readings in a row that breach threshold before firing — reduces noisy false alerts
#   Alert suppression: after an alert fires, silence it for N seconds to avoid alert storms
#   This file is mostly software logic — no deep trading knowledge required

from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Metric:
    name: str
    value: float
    timestamp: int


@dataclass
class Alert:
    metric_name: str
    value: float
    threshold: float
    timestamp: int


class AlertMonitor:
    def __init__(self, thresholds: dict[str, float], min_consecutive: int = 2) -> None:
        self.thresholds = thresholds
        self.min_consecutive = min_consecutive
        self.consecutive_counts: dict[str, int] = defaultdict(int)
        self.fired_alerts: list[Alert] = []

    def process(self, metric: Metric) -> Alert | None:
        if metric.name not in self.thresholds:
            return None

        threshold = self.thresholds[metric.name]

        if metric.value < threshold:
            self.consecutive_counts[metric.name] += 1

            if self.consecutive_counts[metric.name] >= self.min_consecutive:
                alert = Alert(
                    metric_name=metric.name,
                    value=metric.value,
                    threshold=threshold,
                    timestamp=metric.timestamp,
                )
                self.fired_alerts.append(alert)
                self.consecutive_counts[metric.name] = 0
                return alert
        else:
            self.consecutive_counts[metric.name] = 0

        return None

    def process_batch(self, metrics: list[Metric]) -> list[Alert]:
        alerts: list[Alert] = []
        for metric in metrics:
            result = self.process(metric)
            if result is not None:
                alerts.append(result)
        return alerts

    def summary(self) -> dict:
        counts: dict[str, int] = defaultdict(int)
        for alert in self.fired_alerts:
            counts[alert.metric_name] += 1
        return dict(counts)


# TODO: Add alert suppression: once an alert fires for a metric, don't fire again for that
#       metric for at least suppression_seconds seconds
# TODO: Add a lower-bound threshold so alerts can fire when a metric drops too low OR rises
#       too high (two-sided alerting)


if __name__ == "__main__":
    thresholds = {
        "cpu_usage":    0.80,
        "memory_usage": 0.90,
        "latency_ms":   500.0,
        "error_rate":   0.05,
    }

    monitor = AlertMonitor(thresholds=thresholds, min_consecutive=2)

    metrics_stream = [
        # cpu going high — should alert after 2 consecutive breaches
        Metric("cpu_usage",    0.85, timestamp=1000),
        Metric("cpu_usage",    0.88, timestamp=1010),
        Metric("cpu_usage",    0.92, timestamp=1020),
        # cpu drops below threshold — counter should reset
        Metric("cpu_usage",    0.70, timestamp=1030),
        Metric("cpu_usage",    0.75, timestamp=1040),
        # latency spike
        Metric("latency_ms",   450.0, timestamp=1050),
        Metric("latency_ms",   520.0, timestamp=1060),
        Metric("latency_ms",   600.0, timestamp=1070),
        # error rate normal
        Metric("error_rate",   0.02, timestamp=1080),
        Metric("error_rate",   0.03, timestamp=1090),
        # memory spike
        Metric("memory_usage", 0.95, timestamp=1100),
        Metric("memory_usage", 0.97, timestamp=1110),
    ]

    print("=== Processing metrics ===")
    for metric in metrics_stream:
        alert = monitor.process(metric)
        status = f"ALERT FIRED: {alert.metric_name}={alert.value}" if alert else "ok"
        print(f"  t={metric.timestamp} {metric.name}={metric.value:.2f} -> {status}")

    print("\n=== Alert Summary ===")
    for name, count in monitor.summary().items():
        print(f"  {name}: {count} alerts")

    print(f"\n  Total alerts fired: {len(monitor.fired_alerts)}")
