"""
Application settings and configuration management.

Uses pydantic-settings for environment variable loading and validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="postgresql+asyncpg://plana:plana@localhost:5432/plana",
        description="Database connection URL",
    )
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    echo: bool = Field(default=False, description="Echo SQL queries")


class RedisSettings(BaseSettings):
    """Redis configuration for caching and task queue."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    cache_ttl_seconds: int = Field(default=3600, description="Default cache TTL")


class StorageSettings(BaseSettings):
    """Document storage configuration."""

    model_config = SettingsConfigDict(env_prefix="STORAGE_")

    backend: Literal["local", "s3"] = Field(
        default="local", description="Storage backend type"
    )
    local_path: Path = Field(
        default=Path("./data/documents"), description="Local storage path"
    )
    s3_bucket: str | None = Field(default=None, description="S3 bucket name")
    s3_region: str = Field(default="eu-west-2", description="S3 region")
    s3_endpoint_url: str | None = Field(
        default=None, description="S3-compatible endpoint URL"
    )
    s3_access_key: SecretStr | None = Field(default=None, description="S3 access key")
    s3_secret_key: SecretStr | None = Field(default=None, description="S3 secret key")


class VectorStoreSettings(BaseSettings):
    """Vector database configuration."""

    model_config = SettingsConfigDict(env_prefix="VECTOR_")

    # Default to "stub" for zero-dependency local development
    # Set to "chroma" for full semantic search with embeddings
    backend: Literal["stub", "chroma", "pinecone", "qdrant"] = Field(
        default="stub", description="Vector store backend (stub for local dev, chroma for production)"
    )
    chroma_persist_path: Path = Field(
        default=Path("./data/chroma"), description="ChromaDB persistence path"
    )
    collection_prefix: str = Field(
        default="plana", description="Collection name prefix"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence transformer model"
    )
    embedding_dimension: int = Field(default=384, description="Embedding dimension")


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: Literal["anthropic", "openai"] = Field(
        default="anthropic", description="LLM provider"
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None, description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514", description="Anthropic model to use"
    )
    openai_api_key: SecretStr | None = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    max_tokens: int = Field(default=4096, description="Max tokens for generation")
    temperature: float = Field(default=0.3, description="Generation temperature")


class CouncilSettings(BaseSettings):
    """Council-specific configuration."""

    model_config = SettingsConfigDict(env_prefix="COUNCIL_")

    default_council: str = Field(
        default="newcastle", description="Default council ID"
    )
    request_delay_seconds: float = Field(
        default=1.0, description="Delay between requests to council portals"
    )
    request_timeout_seconds: int = Field(
        default=30, description="Request timeout"
    )
    max_retries: int = Field(default=3, description="Max retry attempts")
    user_agent: str = Field(
        default="Plana.AI Planning Research Bot/1.0 (+https://plana.ai)",
        description="User agent for requests",
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        env_prefix="PLANA_",
    )

    # Application
    app_name: str = Field(default="Plana.AI", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Local development mode
    use_fixtures: bool = Field(
        default=True,
        description="Use fixture data instead of live portal (for offline development)",
    )
    skip_llm: bool = Field(
        default=False,
        description="Skip LLM calls and return template responses (for testing)",
    )

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    cors_origins: list[str] = Field(
        default=["*"], description="CORS allowed origins"
    )

    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    council: CouncilSettings = Field(default_factory=CouncilSettings)

    # Paths
    data_dir: Path = Field(default=Path("./data"), description="Data directory")
    logs_dir: Path = Field(default=Path("./logs"), description="Logs directory")
    prompts_dir: Path = Field(
        default=Path("./prompts"), description="Prompts directory"
    )

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        for path in [
            self.data_dir,
            self.logs_dir,
            self.prompts_dir,
            self.storage.local_path,
            self.vector_store.chroma_persist_path,
        ]:
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings
