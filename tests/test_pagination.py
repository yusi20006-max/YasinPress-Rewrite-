from yasinpress.api.pagination import CollectionPage, Page

def test_page_normalizes_invalid_and_large_values() -> None:
    page = Page.from_query("-4", "1000")
    assert page.number == 1
    assert page.size == 100
    assert page.offset == 0

def test_collection_page_serializes_metadata() -> None:
    page = Page(2, 10)
    result = CollectionPage([{"news_id": "YP-1"}], page, 21).as_dict()
    assert result["items"] == [{"news_id": "YP-1"}]
    assert result["pagination"] == {"page": 2, "size": 10, "total": 21, "pages": 3}
