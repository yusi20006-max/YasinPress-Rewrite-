import pytest

from yasinpress.publishing.registry import PublisherRegistry


class Publisher:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


def test_registry_normalizes_names_and_lists_deterministically():
    registry = PublisherRegistry([Publisher(" Eitaa "), Publisher("rss")])
    assert registry.names() == ("eitaa", "rss")
    assert registry.get(" EITAA ").name == " Eitaa "


def test_registry_rejects_duplicates():
    registry = PublisherRegistry()
    registry.register(Publisher("eitaa"))
    with pytest.raises(ValueError):
        registry.register(Publisher(" EITAA "))


def test_registry_missing_destination_is_explicit():
    registry = PublisherRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.get("eitaa")
