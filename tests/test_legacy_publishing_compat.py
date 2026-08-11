from yasinpress.publishing import Publisher, PublishResult
from yasinpress.publishing.base import Publisher as LegacyPublisher
from yasinpress.publishing.base import PublishResult as LegacyPublishResult


def test_legacy_publishing_module_points_to_canonical_contract():
    assert LegacyPublisher is Publisher
    assert LegacyPublishResult is PublishResult
