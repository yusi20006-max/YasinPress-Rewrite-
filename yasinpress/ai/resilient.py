from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass

from yasinpress.database.models import Article
from yasinpress.ai.base import AIProvider, AIResult


@dataclass(frozen=True)
class AIResiliencePolicy:
    timeout_seconds: float = 20.0
    max_attempts: int = 2


class ResilientAIProvider(AIProvider):
    """Provider adapter that isolates timeout/failure from the core pipeline."""

    def __init__(self, provider: AIProvider, policy: AIResiliencePolicy | None = None) -> None:
        self.provider = provider
        self.policy = policy or AIResiliencePolicy()
        if self.policy.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.policy.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

    @property
    def name(self) -> str:
        return self.provider.name

    def enrich(self, article: Article) -> AIResult:
        last_error = "AI provider failed"
        for _ in range(self.policy.max_attempts):
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self.provider.enrich, article)
            try:
                result = future.result(timeout=self.policy.timeout_seconds)
                if not isinstance(result, AIResult):
                    return AIResult(article.title, article.content, self.name, False, "Invalid AI provider response")
                return result
            except FutureTimeoutError:
                last_error = f"AI provider timeout after {self.policy.timeout_seconds:g}s"
                future.cancel()
            except Exception as exc:
                last_error = f"AI provider failure: {exc}"
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        return AIResult(article.title, article.content, self.name, False, last_error)
