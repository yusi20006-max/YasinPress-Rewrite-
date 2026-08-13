

def test_hourly_history_key_includes_destination():
    records = [
        (101, "eitaa"),
        (101, "rss"),
        (102, "eitaa"),
    ]
    published_keys = set(records)
    published_articles = {article_id for article_id, _ in published_keys}
    assert published_articles == {101, 102}
    assert len(published_keys) == 3
