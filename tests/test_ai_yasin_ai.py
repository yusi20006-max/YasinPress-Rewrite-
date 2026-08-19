import sys
import types
from datetime import UTC, datetime

from yasinpress.ai.base import AIResult
from yasinpress.ai.yasin_ai import YasinAIProvider
from yasinpress.database.models import Article


class FakeGenerationResult:
    def __init__(self, text: str, success: bool = True, error: str | None = None):
        self.text = text
        self.success = success
        self.error = error
        self.model = "test-model"
        self.provider = "fake-yasin-ai"


class FakeGenerationService:
    def __init__(self, result: FakeGenerationResult):
        self.result = result
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return self.result


def article() -> Article:
    return Article(
        id="YSN-1",
        title="عنوان اصلی",
        url="https://example.com/1",
        content="متن اصلی",
        source="Example",
        published_at=datetime.now(UTC),
    )


def install_fake_public_contract(monkeypatch):
    package = types.ModuleType("yasinai")
    contracts = types.ModuleType("yasinai.contracts")

    class GenerationRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    contracts.GenerationRequest = GenerationRequest
    package.contracts = contracts
    monkeypatch.setitem(sys.modules, "yasinai", package)
    monkeypatch.setitem(sys.modules, "yasinai.contracts", contracts)


def test_yasin_ai_adapter_uses_public_generation_contract(monkeypatch):
    install_fake_public_contract(monkeypatch)
    service = FakeGenerationService(
        FakeGenerationResult(
            '{"title":"عنوان بازنویسی","content":"متن بازنویسی",'
            '"summary":"خلاصه","category":"politics","priority":"high","breaking":true}'
        )
    )
    result = YasinAIProvider(service, model="test-model").enrich(article())

    assert isinstance(result, AIResult)
    assert result.success
    assert result.provider == "fake-yasin-ai"
    assert result.title == "عنوان بازنویسی"
    assert result.content == "متن بازنویسی"
    assert result.category == "politics"
    assert result.priority == "high"
    assert result.breaking is True
    assert result.metadata["yasin_ai_version"] == "1.1.4"
    assert service.requests[0].model == "test-model"


def test_yasin_ai_adapter_rejects_invalid_structured_response(monkeypatch):
    install_fake_public_contract(monkeypatch)
    service = FakeGenerationService(FakeGenerationResult("not-json"))
    result = YasinAIProvider(service).enrich(article())

    assert not result.success
    assert result.title == "عنوان اصلی"
    assert result.content == "متن اصلی"
    assert result.error == "Invalid Yasin-AI structured response"


def test_yasin_ai_adapter_contains_generation_failure(monkeypatch):
    install_fake_public_contract(monkeypatch)
    service = FakeGenerationService(
        FakeGenerationResult("", success=False, error="provider timeout")
    )
    result = YasinAIProvider(service).enrich(article())

    assert not result.success
    assert result.error == "provider timeout"
    assert result.provider == "yasin-ai"
