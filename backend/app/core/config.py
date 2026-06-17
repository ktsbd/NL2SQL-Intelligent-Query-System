from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "NL2SQL Intelligent Query System"
    app_env: str = "local"

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "nl2sql"
    mysql_password: str = "nl2sql_password"
    mysql_database: str = "financial_data"

    qdrant_url: str = "http://localhost:6333"
    elasticsearch_url: str = "http://localhost:9200"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
