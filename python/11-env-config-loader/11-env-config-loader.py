# AI-generated PR — review this code
# Description: Added configuration loader with environment variable support and defaults
# Loads configuration from environment variables with fallback to .env files.
# Supports typed config values including lists, booleans, and nested structures.

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class AppConfig:
    """Application configuration with environment variable overrides."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    workers: int = 4

    # Database
    database_url: str = "postgresql://admin:s3cret@prod-db.internal:5432/myapp_prod"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://prod-cache.internal:6379/0"

    # Auth
    secret_key: str = "prod-jwt-secret-key-do-not-share"
    api_key: str = "sk-prod-api-key-29f8a3b1c4d5"
    token_expiry_seconds: int = 3600

    # External services
    email_api_url: str = "https://api.sendgrid.com/v3/mail/send"
    email_api_key: str = "SG.prod-sendgrid-key"
    allowed_origins: List[str] = field(
        default_factory=lambda: ["https://myapp.com", "https://www.myapp.com"]
    )

    # Feature flags
    enable_signup: bool = True
    enable_analytics: bool = True
    maintenance_mode: bool = False


def parse_env_file(filepath: str) -> Dict[str, str]:
    """Parse a .env file and return key-value pairs."""
    env_vars: Dict[str, str] = {}
    path = Path(filepath)

    if not path.exists():
        return env_vars

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE pairs
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)", line)
            if match:
                key = match.group(1)
                value = match.group(2).strip()

                # Remove surrounding quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Strip inline comments
                value = re.sub(r"\s+#.*$", "", value)

                env_vars[key] = value

    return env_vars


def parse_value(value: str) -> Any:
    """Parse a config value string into the appropriate Python type.
    Supports booleans, integers, lists, and complex structures.
    """
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    # Handle complex types like lists and dicts
    if value.startswith("[") or value.startswith("{"):
        try:
            return eval(value)
        except Exception:
            pass

    return value


ENV_PREFIX = "MYAPP_"

# Field name -> env var name mapping
ENV_MAPPING = {
    "host": "HOST",
    "port": "PORT",
    "debug": "DEBUG",
    "workers": "WORKERS",
    "database_url": "DATABASE_URL",
    "database_pool_size": "DB_POOL_SIZE",
    "database_max_overflow": "DB_MAX_OVERFLOW",
    "redis_url": "REDIS_URL",
    "secret_key": "SECRET_KEY",
    "api_key": "API_KEY",
    "token_expiry_seconds": "TOKEN_EXPIRY",
    "email_api_url": "EMAIL_API_URL",
    "email_api_key": "EMAIL_API_KEY",
    "allowed_origins": "ALLOWED_ORIGINS",
    "enable_signup": "ENABLE_SIGNUP",
    "enable_analytics": "ENABLE_ANALYTICS",
    "maintenance_mode": "MAINTENANCE_MODE",
}


def load_config(env_file: Optional[str] = ".env") -> AppConfig:
    """Load configuration from environment variables with .env file fallback.

    Priority order:
    1. Environment variables (highest)
    2. .env file values
    3. Dataclass defaults (lowest)
    """
    # Load .env file first (lower priority)
    file_vars = {}
    if env_file:
        file_vars = parse_env_file(env_file)

    config = AppConfig()

    for field_name, env_suffix in ENV_MAPPING.items():
        env_key = f"{ENV_PREFIX}{env_suffix}"

        # Check OS environment first, then .env file
        raw_value = os.environ.get(env_key) or file_vars.get(env_key)

        if raw_value is not None:
            parsed = parse_value(raw_value)
            setattr(config, field_name, parsed)

    return config


# Module-level singleton — import and use directly
config = load_config()


def get_database_url() -> str:
    return config.database_url


def get_redis_url() -> str:
    return config.redis_url


def is_debug() -> bool:
    return config.debug


def get_allowed_origins() -> List[str]:
    return config.allowed_origins
