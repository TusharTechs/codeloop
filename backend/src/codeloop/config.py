"""Runtime configuration, validated at startup. Every value can be set by environment variable."""

from __future__ import annotations

from functools import cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .domain.models import PromptPolicy

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_prefix="", extra="ignore")

    # AssemblyAI
    assemblyai_api_key: SecretStr = Field(default=SecretStr(""))
    streaming_url: str = "wss://streaming.assemblyai.com/v3/ws"
    agent_url: str = "wss://agents.assemblyai.com/v1/ws"
    speech_model: str = "universal-3-5-pro"
    # Measured on day 1: 160/640 ms cut event latency p50 from 4.4 s to 1.4 s with no loss of
    # loop outcomes (docs/spike-findings.md).
    min_turn_silence_ms: int = 160
    max_turn_silence_ms: int = 640
    max_speakers: int = 6
    language_codes: list[str] = ["en", "hi"]
    medical_mode: bool = True
    voice_focus: str = "far-field"
    agent_voice: str = "michael"
    agent_enabled: bool = True

    # Clinical behaviour
    prompt_policy: PromptPolicy = PromptPolicy.TIMERS_AND_LOOPS
    low_confidence: float = 0.6

    # Operations and safety limits
    access_token: SecretStr | None = None  # when set, every API and WebSocket call must present it
    max_concurrent_codes: int = 4
    max_code_minutes: int = 60
    database_path: Path = REPO_ROOT / "data" / "codeloop.db"
    replay_dir: Path = REPO_ROOT / "demo" / "scenarios"
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    frontend_dist: Path = REPO_ROOT / "frontend" / "dist"

    @property
    def has_api_key(self) -> bool:
        return bool(self.assemblyai_api_key.get_secret_value().strip())


@cache
def get_settings() -> Settings:
    return Settings()
