from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LangSmith (read by the langsmith SDK directly from the environment in later phases)
    langsmith_api_key: str = ""
    langsmith_tracing: bool = False
    langsmith_project: str = "crtc-copilot-dev"

    # LLM / embeddings (used from Phase 3-4)
    google_api_key: str = ""
    llm_model: str = ""
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # Database
    database_url: str = "postgresql+asyncpg://crtc:crtc@localhost:5433/crtc"

    # Auth
    google_client_id: str
    session_secret: str = Field(min_length=32)
    allowed_emails: str = ""
    frontend_origin: str = "http://localhost:3000"

    @property
    def allowed_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_emails.split(",") if e.strip()}

    @property
    def cookie_secure(self) -> bool:
        return self.frontend_origin.startswith("https://")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
