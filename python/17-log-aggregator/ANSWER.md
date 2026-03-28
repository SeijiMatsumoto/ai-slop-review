# 17 — Log Aggregator (Python)

**Categories:** Memory Management, Security (ReDoS), File Handling, Data Integrity

## Bug 1: Reads Entire File into Memory

In `parse_file`, the entire file is read at once with `f.read()`:

```python
content = f.read()
lines = content.split("\n")
```

For large log files (gigabytes in production), this will consume all available memory and crash the process. Log files are one of the most common cases of extremely large files.

**Fix:** Read line by line:

```python
with open(filepath, "r") as f:
    for line in f:
        self._process_line(line.rstrip("\n"))
```

## Bug 2: ReDoS via User-Supplied Regex Patterns

The `add_pattern` method accepts arbitrary regex from users, and these are compiled and executed against every log line in `_process_line`:

```python
custom_match = re.search(pattern, message)
```

A malicious or poorly written pattern like `(a+)+$` can cause catastrophic backtracking (ReDoS), freezing the aggregator for minutes or hours on a single log line. This is a denial-of-service vulnerability.

**Fix:** Validate or sanitize user patterns, set a regex timeout, or use a regex engine that doesn't backtrack (like Google's RE2 via the `re2` Python package):

```python
import re2
custom_match = re2.search(pattern, message)
```

## Bug 3: Unclosed File Handle — No Context Manager

In `parse_file`, the file is opened but never closed:

```python
f = open(filepath, "r")
content = f.read()
```

There is no `f.close()` call and no `with` statement. When processing many files (e.g., `parse_directory`), this leaks file descriptors, eventually hitting the OS limit and causing `OSError: Too many open files`.

**Fix:** Use a context manager:

```python
with open(filepath, "r") as f:
    for line in f:
        ...
```

## Bug 4: Timestamp Parsing Assumes No Timezone

The timestamp is parsed with a fixed format that has no timezone:

```python
timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
```

This creates naive datetime objects. If logs come from servers in different timezones, the timestamps are silently treated as if they are all in the same timezone. Error timelines and metrics will be inaccurate. Logs with timezone info like `2024-01-15 14:30:00+00:00` will fail to parse and the line will be silently dropped.

**Fix:** Use a more flexible parser that handles timezones:

```python
from dateutil import parser
timestamp = parser.parse(timestamp_str)
```

## Bug 5: Silently Drops Malformed Lines Without Counting

In `_process_line`, if a line doesn't match the log pattern, it is silently skipped with a bare `return`:

```python
if not match:
    return
```

The line was already counted in `total_lines`, but there is no tracking of how many lines failed to parse. If 50% of lines are in a slightly different format, the metrics will look perfectly fine but only represent half the data. The `error_rate` calculation will also be wrong because the denominator includes lines that were never actually analyzed.

**Fix:** Track malformed lines separately:

```python
if not match:
    self.metrics["malformed_lines"] = self.metrics.get("malformed_lines", 0) + 1
    return
```
