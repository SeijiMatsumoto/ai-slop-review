# Environment Config Loader — Bugs

## Bug 1: Falls Back to Hardcoded Production Defaults
**Location:** `AppConfig` dataclass defaults (lines ~18-43)

When environment variables are missing (e.g., running locally without a `.env` file), the config falls through to the dataclass defaults, which contain **production values**:
- `database_url = "postgresql://admin:s3cret@prod-db.internal:5432/myapp_prod"`
- `redis_url = "redis://prod-cache.internal:6379/0"`
- `secret_key = "prod-jwt-secret-key-do-not-share"`
- `api_key = "sk-prod-api-key-29f8a3b1c4d5"`

A developer running the app locally without setting up their `.env` file will silently connect to production databases and services. Defaults should be safe local/development values, or the app should raise an error if required variables are missing.

## Bug 2: `eval()` on Config Values (Remote Code Execution)
**Location:** `parse_value()` function, line `return eval(value)`

When a config value starts with `[` or `{`, the function uses Python's `eval()` to parse it. If an attacker can control an environment variable (common in shared hosting, CI/CD, or container orchestration), they can set it to something like `[__import__('os').system('rm -rf /')]` and achieve arbitrary code execution. The fix is to use `json.loads()` or `ast.literal_eval()` instead of `eval()`.

## Bug 3: Secrets Exposed in `__repr__`
**Location:** `AppConfig` dataclass (line ~14)

The `@dataclass` decorator auto-generates a `__repr__` that includes **all fields** by default. If the config object is ever logged (e.g., `logger.info(f"Loaded config: {config}")` or appears in a traceback), it will print `database_url`, `secret_key`, `api_key`, `email_api_key`, and other sensitive values in plaintext. The fix is to define a custom `__repr__` that redacts sensitive fields, or use `repr=False` on sensitive fields.

## Bug 4: `.env` File Parsed with Naive Regex
**Location:** `parse_env_file()` function (lines ~50-79)

The hand-rolled `.env` parser has several issues:
- **Values containing `=`** are truncated. The regex `^([A-Za-z_][A-Za-z0-9_]*)=(.*)` uses `(.*)` for the value, which works, but the inline comment stripping `re.sub(r"\s+#.*$", "", value)` will break values containing ` #` (e.g., `DATABASE_URL=postgres://user:p#ssword@host/db` becomes `DATABASE_URL=postgres://user:p`).
- **Quoted values with `#`** are also broken because the comment stripping happens *after* quote removal.
- A proper `.env` parser (like `python-dotenv`) handles these edge cases. The naive regex approach silently corrupts values.

## Bug 5: Config Is a Mutable Global Singleton
**Location:** `config = load_config()` (line ~146)

The config is loaded once at module import time and stored as a mutable module-level variable. This causes several problems:
- Any code anywhere can do `from env_config_loader import config; config.database_url = "something_else"` and it silently affects all other code using the config.
- It makes testing difficult — tests that modify config bleed into other tests.
- The config is loaded at import time, so it cannot be easily reconfigured for different environments in the same process.
The fix is to make the config immutable (use `frozen=True` on the dataclass) and/or provide a function-based access pattern that can be overridden in tests.
