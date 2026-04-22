"""集中配置 — 全部通过环境变量注入,无硬编码。"""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- App ----
    APP_NAME: str = "ai-payment-anomaly-backend"
    APP_ENV: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"

    # ---- Data / Storage ----
    # DATA_DIR keeps generated ML/cache artifacts. STORAGE_DIR keeps business
    # seed/runtime data exactly as described in backend-design-v1.md.
    DATA_DIR: str = "./data"
    STORAGE_DIR: str = "./storage"
    MOCK_ORDER_COUNT: int = 1200
    MOCK_RECON_COUNT: int = 480
    MOCK_DATA_ENABLED: bool = True
    SEED_DEFAULT_CONFIG: bool = True
    RANDOM_SEED: int = 20260421

    # ---- LLM ----
    LLM_PROVIDER: str = ""  # openai | qwen | deepseek | mock | "" (auto)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    DASHSCOPE_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen-max"
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ---- ML ----
    ML_AUTO_TRAIN_ON_START: bool = False
    ML_RETRAIN_CRON: str = "0 3 * * *"

    # ---- Agent ----
    AGENT_DEFAULT_TEMPERATURE: float = 0.3
    AGENT_MAX_TOKENS: int = 2048
    AGENT_TIMEOUT_SECONDS: int = 60
    AGENT_TRIGGER_SCORE: int = 70

    # ---- Derived paths ----
    @property
    def data_path(self) -> Path:
        p = Path(self.DATA_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def seed_path(self) -> Path:
        p = self.storage_path / "seeds"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def runtime_path(self) -> Path:
        p = self.storage_path / "runtime"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def models_path(self) -> Path:
        p = self.data_path / "models"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def vectors_path(self) -> Path:
        p = self.storage_path / "kb" / "faiss_index"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def kb_path(self) -> Path:
        p = self.storage_path / "kb"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cache_path(self) -> Path:
        p = self.data_path / "cache"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
