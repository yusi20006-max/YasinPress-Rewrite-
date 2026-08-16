from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AIConfig:
    enabled: bool = False
    provider: str = "yasin-ai"
    base_url: str = "https://api.openai.com/v1"
    model: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 30.0

    @property
    def api_key(self) -> str | None:
        return os.getenv(self.api_key_env)

    def usable(self) -> bool:
        if not self.enabled:
            return False
        if self.provider == "yasin-ai":
            return True
        return bool(self.api_key) and bool(self.base_url) and bool(self.model)

    @classmethod
    def from_env(cls) -> AIConfig:
        enabled = os.getenv("YASINPRESS_AI_ENABLED", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return cls(
            enabled=enabled,
            provider=os.getenv("YASINPRESS_AI_PROVIDER", cls.provider).strip().lower(),
            base_url=os.getenv("YASINPRESS_AI_BASE_URL", cls.base_url),
            model=os.getenv("YASINPRESS_AI_MODEL") or cls.model,
            api_key_env=os.getenv("YASINPRESS_AI_API_KEY_ENV", cls.api_key_env),
            timeout_seconds=float(os.getenv("YASINPRESS_AI_TIMEOUT", str(cls.timeout_seconds))),
        )
