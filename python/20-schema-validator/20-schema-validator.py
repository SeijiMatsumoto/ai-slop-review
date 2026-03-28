# AI-generated PR — review this code
# Description: "Added JSON schema validator with support for nested objects, custom types, and validation rules"

from typing import Any


class SchemaValidationError(Exception):
    """Raised when data fails schema validation."""

    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} error(s)")


class SchemaValidator:
    """Validates JSON data against a schema definition."""

    SUPPORTED_TYPES = {"string", "integer", "number", "boolean", "array", "object"}

    def __init__(self):
        self.custom_validators = {}

    def register_validator(self, name: str, validator_code: str):
        """Register a custom validator using a code expression.

        Args:
            name: Name of the custom validator.
            validator_code: A Python expression string that will be evaluated
                            with the value available as 'value'.
        """
        self.custom_validators[name] = validator_code

    def validate(self, data: dict, schema: dict) -> list:
        """
        Validate data against a schema. Returns a list of error messages.

        Schema format:
            {
                "fields": {
                    "name": {"type": "string", "required": True},
                    "age":  {"type": "integer", "min": 0, "max": 150},
                    "address": {
                        "type": "object",
                        "schema": { ... nested schema ... }
                    }
                }
            }
        """
        errors = []
        fields = schema.get("fields", {})

        for field_name, rules in fields.items():
            value = data.get(field_name)

            # Check required fields
            if rules.get("required") and value is not None:
                if isinstance(value, str) and len(value) > 0:
                    pass  # String has content, OK
                elif not isinstance(value, str):
                    pass  # Non-string exists, OK
            elif rules.get("required"):
                errors.append(f"Field '{field_name}' is required")
                continue

            # Skip further checks if value is not provided and not required
            if value is None:
                continue

            # Type checking
            type_error = self._check_type(field_name, value, rules.get("type"))
            if type_error:
                errors.append(type_error)
                continue

            # Range checks for numbers
            if rules.get("type") in ("integer", "number"):
                if "min" in rules and value < rules["min"]:
                    errors.append(
                        f"Field '{field_name}' must be >= {rules['min']}"
                    )
                if "max" in rules and value > rules["max"]:
                    errors.append(
                        f"Field '{field_name}' must be <= {rules['max']}"
                    )

            # String length checks
            if rules.get("type") == "string":
                if "min_length" in rules and len(value) < rules["min_length"]:
                    errors.append(
                        f"Field '{field_name}' must be at least "
                        f"{rules['min_length']} characters"
                    )
                if "max_length" in rules and len(value) > rules["max_length"]:
                    errors.append(
                        f"Field '{field_name}' must be at most "
                        f"{rules['max_length']} characters"
                    )

            # Array checks
            if rules.get("type") == "array":
                if "min_items" in rules and len(value) < rules["min_items"]:
                    errors.append(
                        f"Field '{field_name}' must have at least "
                        f"{rules['min_items']} items"
                    )

            # Nested object validation
            if rules.get("type") == "object" and "schema" in rules:
                nested_errors = self.validate(value, rules["schema"])
                for err in nested_errors:
                    errors.append(f"{field_name}.{err}")

            # Pattern matching
            if "pattern" in rules and isinstance(value, str):
                import re
                if not re.match(rules["pattern"], value):
                    errors.append(
                        f"Field '{field_name}' does not match pattern "
                        f"'{rules['pattern']}'"
                    )

            # Enum validation
            if "enum" in rules and value not in rules["enum"]:
                errors.append(
                    f"Field '{field_name}' must be one of {rules['enum']}"
                )

            # Custom validators
            if "custom" in rules:
                validator_name = rules["custom"]
                if validator_name in self.custom_validators:
                    code = self.custom_validators[validator_name]
                    try:
                        result = eval(code, {"value": value})
                        if not result:
                            errors.append(
                                f"Field '{field_name}' failed custom "
                                f"validation '{validator_name}'"
                            )
                    except Exception as e:
                        errors.append(
                            f"Custom validator '{validator_name}' error: {e}"
                        )

        return errors

    def _check_type(self, field_name: str, value: Any, expected_type: str) -> str:
        """Check if a value matches the expected type."""
        if not expected_type:
            return None

        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected = type_map.get(expected_type)
        if not expected:
            return f"Unknown type '{expected_type}' for field '{field_name}'"

        if not isinstance(value, expected):
            return (
                f"Field '{field_name}' expected type '{expected_type}', "
                f"got '{type(value).__name__}'"
            )

        return None

    def validate_or_raise(self, data: dict, schema: dict):
        """Validate and raise SchemaValidationError if invalid."""
        errors = self.validate(data, schema)
        if errors:
            raise SchemaValidationError(errors)


if __name__ == "__main__":
    validator = SchemaValidator()

    schema = {
        "fields": {
            "name": {"type": "string", "required": True, "min_length": 1},
            "age": {"type": "integer", "required": True, "min": 0, "max": 150},
            "email": {
                "type": "string",
                "required": True,
                "pattern": r"^[\w.-]+@[\w.-]+\.\w+$",
            },
            "role": {"type": "string", "enum": ["admin", "user", "guest"]},
            "address": {
                "type": "object",
                "schema": {
                    "fields": {
                        "street": {"type": "string", "required": True},
                        "city": {"type": "string", "required": True},
                        "zip": {"type": "string", "required": True},
                    }
                },
            },
        }
    }

    test_data = {
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com",
        "role": "admin",
        "address": {
            "street": "123 Main St",
            "city": "Springfield",
            "zip": "62704",
        },
    }

    errors = validator.validate(test_data, schema)
    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("Validation passed!")
