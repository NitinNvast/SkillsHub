"""Application settings loaded from env vars.

AI configuration is provider-agnostic:
  - LLM_PROVIDER / LLM_MODEL              : default chat/reasoning route
  - FALLBACK_LLM_PROVIDER / FALLBACK_LLM_MODEL : retry target on primary failure
  - EMBEDDING_PROVIDER / EMBEDDING_MODEL   : embedding route
  - Per-task overrides (each falls back to LLM_*) :
      EXTRACTION_PROVIDER / EXTRACTION_MODEL
      INFERENCE_PROVIDER / INFERENCE_MODEL
      PARSING_PROVIDER   / PARSING_MODEL
      RERANK_PROVIDER    / RERANK_MODEL

The legacy `extraction_model`, `light_model`, `rerank_model` fields are kept
as aliases for the new per-task model fields so existing .env files continue
to work without modification.
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

    # ─── AI provider API keys (only the ones you use need to be set) ──
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    gemini_api_key: str | None = None
    openrouter_api_key: str | None = None
    voyage_api_key: str | None = None

    # ─── Default chat/reasoning route ──────────────────────
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"

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
    extraction_model: str | None = "claude-sonnet-4-6"  # legacy default
    inference_provider: str | None = None
    inference_model: str | None = None
    parsing_provider: str | None = None
    parsing_model: str | None = None
    rerank_provider: str | None = None
    rerank_model: str | None = "claude-sonnet-4-6"  # legacy default
    # `light_model` was the legacy name for the Haiku model used by inference + parsing.
    light_model: str | None = "claude-haiku-4-5-20251001"

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
