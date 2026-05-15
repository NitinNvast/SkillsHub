"""Application settings loaded from env vars."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Database ──────────────────────────────────────────
    database_url: str

    # ─── Auth ──────────────────────────────────────────────
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 1 day

    # ─── AI providers ──────────────────────────────────────
    anthropic_api_key: str
    voyage_api_key: str

    # ─── Model assignments ─────────────────────────────────
    # Heavy quality work (extraction, reasoning, re-rank)
    extraction_model: str = "claude-sonnet-4-6"
    rerank_model: str = "claude-sonnet-4-6"
    # Cheap/fast work (skill inference, query parsing)
    light_model: str = "claude-haiku-4-5-20251001"
    # Embeddings (1024-dim cosine via pgvector HNSW)
    embedding_model: str = "voyage-3-large"
    embedding_dim: int = 1024

    # ─── CORS ──────────────────────────────────────────────
    allowed_origins: str = ""  # comma-separated extra origins

    # ─── Uploads ───────────────────────────────────────────
    upload_dir: str = "uploads"

    # ─── Search ────────────────────────────────────────────
    search_top_k_retrieval: int = 20  # vector pre-filter
    search_top_k_rerank: int = 8  # final results shown to user


settings = Settings()  # type: ignore[call-arg]
