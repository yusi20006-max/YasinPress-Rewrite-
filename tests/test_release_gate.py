from yasinpress import __version__
from yasinpress.publishing import PublishResult, Publisher


def test_release_contract_is_available():
    assert __version__
    assert Publisher is not None
    assert PublishResult is not None
