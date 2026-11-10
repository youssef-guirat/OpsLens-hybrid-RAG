from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OPSLENS_",
        extra="ignore",
    )

    source_dir: Path = Path("data/documents")
    index_path: Path = Path("data/index/index.json")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    enable_reranker: bool = True
    dense_top_k: int = Field(default=12, ge=1, le=100)
    sparse_top_k: int = Field(default=12, ge=1, le=100)
    final_top_k: int = Field(default=5, ge=1, le=20)
    rrf_k: int = Field(default=60, ge=1)
    log_level: str = "INFO"

    # These intentionally do not use the OPSLENS_ prefix so standard provider
    # environment variables work unchanged.
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", validation_alias="OPENAI_MODEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

