# 20 — Schema Validator (Python)

**Categories:** Security, Type Safety, Edge Cases, Recursion

## Bug 1: `bool` Passes as `int` Due to Python's Type Hierarchy

In `_check_type`, the type check for `"integer"` uses `isinstance(value, int)`. In Python, `bool` is a subclass of `int`, so `isinstance(True, int)` returns `True`. This means `True` and `False` silently pass validation for integer fields. For example, `{"age": True}` would be considered valid and `True` would be treated as `1` in subsequent range checks.

**Fix:** Check for `bool` explicitly before checking `int`:

```python
if expected_type == "integer" and isinstance(value, bool):
    return f"Field '{field_name}' expected type 'integer', got 'boolean'"
```

## Bug 2: No Max Recursion Depth for Nested Schemas — Stack Overflow

The `validate` method calls itself recursively for nested `"object"` schemas:

```python
if rules.get("type") == "object" and "schema" in rules:
    nested_errors = self.validate(value, rules["schema"])
```

There is no depth limit. A deeply nested schema (or a schema that contains a circular reference) will cause infinite recursion and crash with a `RecursionError` / stack overflow. An attacker providing a malicious schema can crash the validator.

**Fix:** Add a depth parameter and enforce a maximum:

```python
def validate(self, data: dict, schema: dict, _depth: int = 0) -> list:
    if _depth > 20:
        return ["Maximum nesting depth exceeded"]
    # ...
    nested_errors = self.validate(value, rules["schema"], _depth + 1)
```

## Bug 3: Empty String Passes Required Field Check

The required field check has inverted logic:

```python
if rules.get("required") and value is not None:
    if isinstance(value, str) and len(value) > 0:
        pass  # String has content, OK
    elif not isinstance(value, str):
        pass  # Non-string exists, OK
```

An empty string `""` hits the `isinstance(value, str)` branch but fails `len(value) > 0`, falling through without adding an error. So `{"name": ""}` passes the required check for a required string field. The whole block is also confusing because it checks the "present" case but does nothing useful with it — the actual logic is just `elif rules.get("required")` which only triggers when `value is None`.

**Fix:** Explicitly reject empty strings for required fields:

```python
if rules.get("required"):
    if value is None or (isinstance(value, str) and len(value) == 0):
        errors.append(f"Field '{field_name}' is required")
        continue
```

## Bug 4: Number Range Checks Don't Handle `None` Values

The range checks for numbers execute whenever the type is `"integer"` or `"number"`:

```python
if rules.get("type") in ("integer", "number"):
    if "min" in rules and value < rules["min"]:
```

If an earlier code path somehow leaves `value` as `None` (for example if the required check is skipped), comparing `None < rules["min"]` will raise a `TypeError` in Python 3. More subtly, this section doesn't guard against the case where `value` passed the type check but is actually a `bool` (due to Bug 1), leading to incorrect comparisons like `True > 150`.

**Fix:** Add a None guard before range checks, and ensure type checking properly excludes booleans.

## Bug 5: Custom Validators Executed with `eval()` — Arbitrary Code Execution

The `register_validator` method stores raw Python code strings, and `validate` executes them with `eval()`:

```python
result = eval(code, {"value": value})
```

Anyone who can register a custom validator can execute arbitrary Python code on the server. For example:

```python
validator.register_validator("evil", "__import__('os').system('rm -rf /')")
```

Even though the namespace is restricted to `{"value": value}`, `__import__` is still accessible via builtins, making the sandbox trivially escapable.

**Fix:** Never use `eval()` with user input. Accept callable functions instead:

```python
def register_validator(self, name: str, validator_fn: callable):
    self.custom_validators[name] = validator_fn

# In validate:
result = self.custom_validators[validator_name](value)
```
