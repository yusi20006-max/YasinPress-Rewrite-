from yasinpress.publishing import PublishResult, Publisher
from yasinpress.publishing.base import PublishResult as LegacyPublishResult
from yasinpress.publishing.base import Publisher as LegacyPublisher


def test_legacy_publishing_module_points_to_canonical_contract():
    assert LegacyPublisher is Publisher
    assert LegacyPublishResult is PublishResult
