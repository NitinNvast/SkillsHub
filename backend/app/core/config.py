"""Application settings loaded from env vars.

AI configuration:
  - LLM_PROVIDER=groq / LLM_MODEL                    : default chat route (Groq only)
  - EMBEDDING_PROVIDER=voyage / EMBEDDING_MODEL       : embedding route (Voyage only)
  - Per-task overrides (each falls back to LLM_*):
      EXTRACTION_MODEL, INFERENCE_MODEL, PARSING_MODEL, RERANK_MODEL
  - LIGHT_MODEL: fast model for inference + parsing tasks
"""

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

    # ─── AI provider API keys ──────────────────────────────
    groq_api_key: str | None = None
    voyage_api_key: str | None = None
    github_token: str | None = None

    # ─── Default chat/reasoning route ──────────────────────
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"

    # ─── Fallback (used on primary provider failure) ───────
    fallback_llm_provider: str | None = None
    fallback_llm_model: str | None = None

    # ─── Embeddings ────────────────────────────────────────
    embedding_provider: str = "voyage"
    embedding_model: str = "voyage-3-large"
    embedding_dim: int = 1024

    # ─── Per-task overrides ────────────────────────────────
    # Each is optional — when unset, the task uses LLM_PROVIDER / LLM_MODEL.
    extraction_provider: str | None = None
    extraction_model: str | None = "llama-3.3-70b-versatile"
    inference_provider: str | None = None
    inference_model: str | None = None
    parsing_provider: str | None = None
    parsing_model: str | None = None
    rerank_provider: str | None = None
    rerank_model: str | None = "llama-3.3-70b-versatile"
    light_model: str | None = "llama-3.1-8b-instant"

    # ─── Reliability ───────────────────────────────────────
    ai_request_timeout: float = 60.0
    ai_max_retries: int = 2

    # ─── CORS ──────────────────────────────────────────────
    allowed_origins: str = ""

    # ─── Uploads ───────────────────────────────────────────
    upload_dir: str = "uploads"

    # ─── Search ────────────────────────────────────────────
    search_top_k_retrieval: int = 20
    search_top_k_rerank: int = 8


settings = Settings()  # type: ignore[call-arg]
