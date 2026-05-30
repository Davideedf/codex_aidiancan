from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise Knowledge Agent"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    data_dir: Path = Path("data")
    max_upload_mb: int = Field(default=10, ge=1, le=100)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def documents_dir(self) -> Path:
        return self.data_dir / "documents"

    @property
    def index_path(self) -> Path:
        return self.data_dir / "knowledge_index.json"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.documents_dir.mkdir(parents=True, exist_ok=True)
    return settings
