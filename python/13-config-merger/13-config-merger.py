# Review this code — find bugs, understand the logic, complete the TODOs

DEFAULTS: dict = {
    "host": "localhost",
    "port": 8080,
    "debug": False,
    "workers": 4,
    "timeout": 30,
    "log_level": "INFO",
    "max_retries": 3,
}


def parse_value(raw: str) -> bool | int | float | str:
    try:
        return int(raw)
    except ValueError:
        pass

    try:
        return float(raw)
    except ValueError:
        pass

    if raw.lower() in ("true", "yes", "1"):
        return True
    if raw.lower() in ("false", "no", "0"):
        return False

    return raw


def merge_configs(*configs: dict) -> dict:
    result = dict(DEFAULTS)

    for config in configs:
        result = config | result

    return result


def load_from_env(prefix: str, env: dict[str, str]) -> dict:
    result: dict = {}
    prefix_upper = prefix.upper() + "_"

    for key, value in env.items():
        if key.upper().startswith(prefix_upper):
            stripped = key[len(prefix_upper):].lower()
            result[stripped] = parse_value(value)

    return result


# TODO: Add support for nested config using dot notation
#       (e.g. "database.host" → {"database": {"host": ...}})
# TODO: Add a validate_config(config: dict, required_keys: list[str]) -> list[str]
#       function that returns missing required keys


if __name__ == "__main__":
    print("=== parse_value ===")
    test_inputs = [
        "42", "3.14", "true", "false", "yes", "no",
        "1", "0", "localhost", "INFO", "8080",
    ]
    for raw in test_inputs:
        parsed = parse_value(raw)
        print(f"  {raw!r:12} -> {parsed!r:10} ({type(parsed).__name__})")

    print("\n=== merge_configs ===")
    base = {"port": 9090, "workers": 8}
    override = {"port": 7070, "debug": True, "log_level": "DEBUG"}

    merged = merge_configs(base, override)
    print(f"  base port: {base['port']}, override port: {override['port']}")
    print(f"  merged port: {merged['port']}")
    print(f"  merged debug: {merged['debug']}")
    print(f"  merged log_level: {merged['log_level']}")
    for k, v in merged.items():
        print(f"    {k}: {v}")

    print("\n=== load_from_env ===")
    env = {
        "APP_HOST": "prod-server.example.com",
        "APP_PORT": "9090",
        "APP_DEBUG": "true",
        "APP_WORKERS": "16",
        "APP_LOG_LEVEL": "WARNING",
        "OTHER_HOST": "should-be-ignored",
    }

    loaded = load_from_env("APP", env)
    print(f"  Loaded {len(loaded)} keys from env:")
    for k, v in loaded.items():
        print(f"    {k}: {v!r} ({type(v).__name__})")

    print("\n=== full merge pipeline ===")
    env_config = load_from_env("APP", env)
    file_config = {"host": "file-override.example.com", "timeout": 60}
    final = merge_configs(env_config, file_config)
    print(f"  Final config:")
    for k, v in final.items():
        print(f"    {k}: {v}")
