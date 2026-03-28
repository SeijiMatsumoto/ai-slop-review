# AI-generated PR — review this code
# Description: "Added log aggregator that parses log files and extracts metrics for monitoring"

import re
import os
import json
from datetime import datetime
from collections import defaultdict


class LogAggregator:
    """Parses log files and extracts metrics such as error rates, response times, etc."""

    LOG_PATTERN = r"^\[(?P<timestamp>[^\]]+)\]\s+(?P<level>\w+)\s+(?P<message>.+)$"

    def __init__(self):
        self.metrics = {
            "total_lines": 0,
            "by_level": defaultdict(int),
            "errors": [],
            "response_times": [],
        }
        self.custom_patterns = {}

    def add_pattern(self, name: str, pattern: str):
        """Register a custom regex pattern for extracting metrics."""
        self.custom_patterns[name] = pattern

    def parse_file(self, filepath: str) -> dict:
        """Parse a log file and extract metrics."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Log file not found: {filepath}")

        f = open(filepath, "r")
        content = f.read()
        lines = content.split("\n")

        for line in lines:
            if not line.strip():
                continue

            self.metrics["total_lines"] += 1
            self._process_line(line)

        return self.metrics

    def _process_line(self, line: str):
        """Process a single log line."""
        match = re.match(self.LOG_PATTERN, line)
        if not match:
            return

        data = match.groupdict()
        level = data["level"].upper()
        timestamp_str = data["timestamp"]
        message = data["message"]

        self.metrics["by_level"][level] += 1

        # Parse timestamp
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        if level == "ERROR":
            self.metrics["errors"].append({
                "timestamp": timestamp.isoformat(),
                "message": message,
            })

        # Extract response time if present
        time_match = re.search(r"response_time=(\d+)ms", message)
        if time_match:
            response_time = int(time_match.group(1))
            self.metrics["response_times"].append(response_time)

        # Run custom patterns
        for name, pattern in self.custom_patterns.items():
            custom_match = re.search(pattern, message)
            if custom_match:
                if name not in self.metrics:
                    self.metrics[name] = []
                self.metrics[name].append(custom_match.group(0))

    def parse_directory(self, dirpath: str, extension: str = ".log") -> dict:
        """Parse all log files in a directory."""
        if not os.path.isdir(dirpath):
            raise NotADirectoryError(f"Not a directory: {dirpath}")

        for filename in os.listdir(dirpath):
            if filename.endswith(extension):
                filepath = os.path.join(dirpath, filename)
                self.parse_file(filepath)

        return self.metrics

    def get_error_rate(self) -> float:
        """Calculate the error rate as a percentage."""
        total = self.metrics["total_lines"]
        errors = self.metrics["by_level"].get("ERROR", 0)
        return (errors / total) * 100

    def get_avg_response_time(self) -> float:
        """Calculate the average response time in milliseconds."""
        times = self.metrics["response_times"]
        if not times:
            return 0.0
        return sum(times) / len(times)

    def get_percentile(self, percentile: int) -> float:
        """Calculate a percentile of response times."""
        times = sorted(self.metrics["response_times"])
        if not times:
            return 0.0
        index = int(len(times) * percentile / 100)
        return times[index]

    def generate_report(self) -> dict:
        """Generate a summary report of all metrics."""
        return {
            "total_lines_processed": self.metrics["total_lines"],
            "log_levels": dict(self.metrics["by_level"]),
            "error_count": len(self.metrics["errors"]),
            "error_rate": self.get_error_rate(),
            "avg_response_time_ms": self.get_avg_response_time(),
            "p95_response_time_ms": self.get_percentile(95),
            "p99_response_time_ms": self.get_percentile(99),
            "recent_errors": self.metrics["errors"][-10:],
        }

    def export_json(self, output_path: str):
        """Export the report as a JSON file."""
        report = self.generate_report()
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report exported to {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python log_aggregator.py <log_file_or_dir> [output.json]")
        sys.exit(1)

    target = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None

    aggregator = LogAggregator()

    if os.path.isdir(target):
        aggregator.parse_directory(target)
    else:
        aggregator.parse_file(target)

    report = aggregator.generate_report()
    print(json.dumps(report, indent=2))

    if output:
        aggregator.export_json(output)
