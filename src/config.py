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

    # Redis
    redis_url: str = "redis://localhost:6379"

    # LLM
    openai_api_key: str = ""

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "slough-contexts"

    # App
    node_env: str = "development"
    log_level: str = "DEBUG"
    port: int = 3000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
