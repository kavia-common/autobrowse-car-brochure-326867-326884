import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables.

    Contract:
      - Inputs: environment variables POSTGRES_* (see db container db_env_vars), optional ADMIN_API_KEY.
      - Outputs: normalized settings object passed to IO/adapters.
      - Errors: raises ValueError if required env vars are missing.
    """

    postgres_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: str

    admin_api_key: str | None


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load and validate environment configuration.

    Required environment variables:
      - POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT

    Optional:
      - ADMIN_API_KEY: if set, admin endpoints require `X-Admin-Key` header.

    Returns:
      Settings: validated settings object.

    Raises:
      ValueError: if any required env var is missing.
    """
    required = ["POSTGRES_URL", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_PORT"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return Settings(
        postgres_url=os.environ["POSTGRES_URL"],
        postgres_user=os.environ["POSTGRES_USER"],
        postgres_password=os.environ["POSTGRES_PASSWORD"],
        postgres_db=os.environ["POSTGRES_DB"],
        postgres_port=os.environ["POSTGRES_PORT"],
        admin_api_key=os.getenv("ADMIN_API_KEY"),
    )
