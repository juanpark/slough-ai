from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Slack
    slack_bot_token: str = ""
    slack_app_token: str = ""
    slack_signing_secret: str = ""
    slack_client_id: str = ""
    slack_client_secret: str = ""

    # Database
    database_url: str = "postgres://postgres:postgres@localhost:5432/slough"

    # Redis (Multi-DB)
    redis_host: str = "localhost"
    redis_port: int = 6379
    dedup_ttl_seconds: int = 60

    @property
    def redis_broker_url(self) -> str:
        """DB0: Celery Broker (Task Queue)."""
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def redis_backend_url(self) -> str:
        """DB1: Celery Backend (Results)."""
        return f"redis://{self.redis_host}:{self.redis_port}/1"

    @property
    def redis_cache_url(self) -> str:
        """DB2: Dedup + Rule Cache."""
        return f"redis://{self.redis_host}:{self.redis_port}/2"

    # LLM
    openai_api_key: str = ""

    # App
    environment: str = "development"
    log_level: str = "DEBUG"
    app_base_url: str = "http://localhost:3000"
    app_port: int = 3000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def postgres_dsn(self) -> str:
        """psycopg3 / AsyncPostgresSaver compatible DSN."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
