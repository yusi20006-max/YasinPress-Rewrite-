import pytest

from yasinpress.publishing.registry import PublisherRegistry


class DummyPublisher:
    name = "dummy"

    def publish(self, article):
        raise NotImplementedError


def test_registry_resolves_destinations():
    publisher = DummyPublisher()
    registry = PublisherRegistry([publisher])
    assert registry.get("DUMMY") is publisher
    assert registry.names() == ("dummy",)


def test_registry_rejects_duplicate_destinations():
    publisher = DummyPublisher()
    with pytest.raises(ValueError):
        PublisherRegistry([publisher, publisher])


def test_registry_rejects_unknown_destination():
    registry = PublisherRegistry()
    with pytest.raises(KeyError):
        registry.get("eitaa")
