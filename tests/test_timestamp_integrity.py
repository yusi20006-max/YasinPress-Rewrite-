import sqlite3
from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article
from yasinpress.database.repositories import ArticleRepository
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.pipeline.application import YasinPressApplication
from yasinpress.pipeline.service import ProcessingService
from yasinpress.processing.freshness import is_fresh
from yasinpress.processing.normalization import normalize
from yasinpress.publishing import PublishResult
from yasinpress.publishing.eitaa import EitaaPublisher
from yasinpress.sources.feed import FeedItem, parse_rss


def test_rss_with_published_at():
    xml = """<rss><channel><item>
        <title>Test News</title>
        <link>https://example.com/news1</link>
        <description>Content</description>
        <pubDate>Tue, 11 Aug 2026 14:30:00 +0330</pubDate>
    </item></channel></rss>"""
    items = parse_rss(xml)
    assert len(items) == 1
    assert items[0].published_at == datetime(2026, 8, 11, 11, 0, 0, tzinfo=UTC)
    assert items[0].updated_at is None


def test_rss_with_updated_at():
    xml = """<rss><channel><item>
        <title>Test News</title>
        <link>https://example.com/news1</link>
        <description>Content</description>
        <updated>Tue, 11 Aug 2026 15:45:00 +0330</updated>
    </item></channel></rss>"""
    items = parse_rss(xml)
    assert len(items) == 1
    # Fallback of published_at to updated_at when pubDate is missing
    assert items[0].published_at == datetime(2026, 8, 11, 12, 15, 0, tzinfo=UTC)
    assert items[0].updated_at == datetime(2026, 8, 11, 12, 15, 0, tzinfo=UTC)


def test_rss_with_both_timestamps():
    xml = """<rss><channel><item>
        <title>Test News</title>
        <link>https://example.com/news1</link>
        <description>Content</description>
        <pubDate>Tue, 11 Aug 2026 14:30:00 +0330</pubDate>
        <updated>Tue, 11 Aug 2026 15:45:00 +0330</updated>
    </item></channel></rss>"""
    items = parse_rss(xml)
    assert len(items) == 1
    assert items[0].published_at == datetime(2026, 8, 11, 11, 0, 0, tzinfo=UTC)
    assert items[0].updated_at == datetime(2026, 8, 11, 12, 15, 0, tzinfo=UTC)


def test_rss_without_timestamp():
    xml = """<rss><channel><item>
        <title>Test News</title>
        <link>https://example.com/news1</link>
        <description>Content</description>
    </item></channel></rss>"""
    items = parse_rss(xml)
    assert len(items) == 1
    assert items[0].published_at == datetime.fromtimestamp(0, tz=UTC)
    assert items[0].updated_at is None


def test_atom_timestamp_parsing():
    xml = """<feed xmlns=\"http://www.w3.org/2005/Atom\"><entry>
        <title>Atom News</title>
        <link href=\"https://example.com/atom1\"/>
        <summary>Summary</summary>
        <published>2026-08-11T14:30:00+03:30</published>
        <updated>2026-08-11T15:45:00+03:30</updated>
    </entry></feed>"""
    items = parse_rss(xml)
    assert len(items) == 1
    assert items[0].published_at == datetime(2026, 8, 11, 11, 0, 0, tzinfo=UTC)
    assert items[0].updated_at == datetime(2026, 8, 11, 12, 15, 0, tzinfo=UTC)


def test_timezone_aware_timestamp_and_normalization():
    item = FeedItem(
        title="Test", url="https://example.com/t", content="Content",
        published_at=datetime(2026, 8, 11, 14, 30, tzinfo=UTC),
        updated_at=datetime(2026, 8, 11, 15, 45, tzinfo=UTC)
    )
    article = normalize(item, "source")
    assert article.published_at == datetime(2026, 8, 11, 14, 30, tzinfo=UTC)
    assert article.updated_at == datetime(2026, 8, 11, 15, 45, tzinfo=UTC)
    assert article.news_timestamp == datetime(2026, 8, 11, 15, 45, tzinfo=UTC) # news_timestamp priority: updated_at -> published_at
    assert article.fetched_at is not None
    assert article.fetched_at.tzinfo == UTC


def test_freshness_gate_boundaries():
    now = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)

    # 1. Newer/recent
    assert is_fresh(now - timedelta(hours=1), now=now)

    # 2. Exactly on the 12-hour boundary
    assert is_fresh(now - timedelta(hours=12), now=now)

    # 3. Older than 12 hours
    assert not is_fresh(now - timedelta(hours=12, seconds=1), now=now)

    # 4. Unknown/missing timestamp
    assert not is_fresh(None, now=now)
    assert not is_fresh(datetime.fromtimestamp(0, tz=UTC), now=now)


def test_prevent_use_of_fetched_at_as_news_timestamp():
    # In normalization, if both published_at and updated_at are None or epoch 0:
    item = FeedItem(
        title="Test", url="https://example.com/t", content="Content",
        published_at=datetime.fromtimestamp(0, tz=UTC),
        updated_at=None
    )
    article = normalize(item, "source")
    # fetched_at must be populated
    assert article.fetched_at is not None
    # but news_timestamp must be None
    assert article.news_timestamp is None
    # and age should be very old (e.g. 999 days)
    assert article.age > timedelta(days=100)


def test_message_rendering_with_timestamps(monkeypatch):
    monkeypatch.setenv("YASINPRESS_TIMEZONE", "Asia/Tehran")
    pub = EitaaPublisher(token="tok", channel="chan")

    # 1. Normal published_at only
    item1 = Article(
        id="YP-123456", title="Title", url="https://example.com", content="Body", source="Source",
        published_at=datetime(2026, 8, 11, 14, 30, tzinfo=UTC)
    )
    msg1 = pub.render(item1)
    assert "زمان خبر: ۲۰ مرداد ۱۴۰۵، ۱۸:۰۰ 🕐" in msg1

    # 2. Updated timestamp present
    item2 = Article(
        id="YP-123456", title="Title", url="https://example.com", content="Body", source="Source",
        published_at=datetime(2026, 8, 11, 14, 30, tzinfo=UTC),
        updated_at=datetime(2026, 8, 11, 15, 45, tzinfo=UTC)
    )
    msg2 = pub.render(item2)
    assert "آخرین به‌روزرسانی: ۲۰ مرداد ۱۴۰۵، ۱۹:۱۵ 🕐" in msg2

    # 3. No valid timestamp
    item3 = Article(
        id="YP-123456", title="Title", url="https://example.com", content="Body", source="Source"
    )
    msg3 = pub.render(item3)
    assert "زمان انتشار: نامشخص 🕐" in msg3


def test_duplicate_and_update_behavior():
    repos = SQLiteRepositories(":memory:")

    class MockEitaaPublisher(EitaaPublisher):
        def publish(self, article):
            return PublishResult(True, self.name)

    app = YasinPressApplication(repositories=repos, publishers=[MockEitaaPublisher(token="t", channel="c")])

    # Ingesting the same news item twice:
    # 1. First fetch
    now = datetime.now(UTC)
    item1 = FeedItem(
        title="Awesome", url="https://example.com/news", content="Body",
        published_at=now - timedelta(minutes=10)
    )
    report1 = app.process_items([item1])
    assert report1.persisted_count == 1

    # Publish pending job to mark it as delivered/published in idempotency store
    results = app.publish_pending()
    assert len(results) == 1
    assert results[0].success is True

    # 2. Second fetch with identical timestamp (duplicate entry)
    report2 = app.process_items([item1])
    assert report2.processing.duplicate_count == 1

    # 3. Fetch with UPDATED timestamp (newer)
    item2 = FeedItem(
        title="Awesome", url="https://example.com/news", content="Body",
        published_at=now - timedelta(minutes=10),
        updated_at=now - timedelta(minutes=5)
    )
    report3 = app.process_items([item2])
    # Should detect as update (not a duplicate!) and persist/process it
    assert report3.processing.duplicate_count == 0
    assert report3.processing.queued_count == 1
    assert report3.persisted_count == 1

    repos.close()


def test_published_to_channel_at_only_on_success():
    repos = SQLiteRepositories(":memory:")

    class MockSuccessPublisher(EitaaPublisher):
        def publish(self, article):
            return PublishResult(True, self.name)

    class MockFailedPublisher(EitaaPublisher):
        def publish(self, article):
            return PublishResult(False, self.name, error="Simulated fail")

    # Success publication
    app_success = YasinPressApplication(repositories=repos, publishers=[MockSuccessPublisher(token="t", channel="c")])
    item = FeedItem(
        title="Success", url="https://example.com/success", content="Body",
        published_at=datetime.now(UTC) - timedelta(minutes=5)
    )
    app_success.process_items([item])
    results = app_success.publish_pending()
    assert len(results) == 1
    assert results[0].success is True

    art_success = app_success.get_article(app_success.repository.all()[0].id)
    assert art_success.published_to_channel_at is not None

    # Failed publication
    app_fail = YasinPressApplication(repositories=repos, publishers=[MockFailedPublisher(token="t", channel="c")])
    item_fail = FeedItem(
        title="Fail", url="https://example.com/fail", content="Body",
        published_at=datetime.now(UTC) - timedelta(minutes=5)
    )
    app_fail.process_items([item_fail])
    results_fail = app_fail.publish_pending()
    assert len(results_fail) == 1
    assert results_fail[0].success is False

    art_fail = next(a for a in app_fail.repository.all() if "fail" in a.url)
    assert art_fail.published_to_channel_at is None

    repos.close()


def test_unknown_to_known_timestamp_transition():
    repos = SQLiteRepositories(":memory:")

    class MockEitaaPublisher(EitaaPublisher):
        def publish(self, article):
            return PublishResult(True, self.name)

    app = YasinPressApplication(repositories=repos, publishers=[MockEitaaPublisher(token="t", channel="c")])

    # 1. Fetch with missing timestamp (lifecycle_state = timestamp_unknown)
    item_unknown = FeedItem(
        title="Unknown", url="https://example.com/unknown", content="Body",
        published_at=datetime.fromtimestamp(0, tz=UTC)
    )
    report1 = app.process_items([item_unknown])
    # Should be saved, but NOT queued (queued_count is 0)
    assert report1.persisted_count == 1
    assert report1.processing.queued_count == 0

    # 2. Fetch again with a VALID/known timestamp
    item_known = FeedItem(
        title="Unknown", url="https://example.com/unknown", content="Body",
        published_at=datetime.now(UTC) - timedelta(minutes=5)
    )
    report2 = app.process_items([item_known])
    # Should be updated, and queued for publication!
    assert report2.processing.duplicate_count == 0
    assert report2.processing.queued_count == 1
    assert report2.persisted_count == 1

    repos.close()


def test_select_fair_batch_sorting_on_news_timestamp():
    class FakeHistory:
        def all(self):
            return ()

    service = ProcessingService(
        source="rss",
        history=FakeHistory(),
        max_publications_per_hour=3,
    )

    # Let's create articles with different news timestamps
    now = datetime.now(UTC)
    # Article A: news_ts = now - 5 min
    art_a = Article(
        id="A", title="A", url="https://example.com/a", content="Body", source="rss",
        published_at=now - timedelta(minutes=5)
    )
    # Article B: news_ts = now - 1 min (newer!)
    art_b = Article(
        id="B", title="B", url="https://example.com/b", content="Body", source="rss",
        published_at=now - timedelta(minutes=1)
    )
    # Article C: news_ts = None (epoch 0, earliest!)
    art_c = Article(
        id="C", title="C", url="https://example.com/c", content="Body", source="rss",
        published_at=datetime.fromtimestamp(0, tz=UTC)
    )

    batch = service._select_fair_batch((art_a, art_b, art_c))
    # Best sorting is B first, then A, then C
    assert batch[0].id == "B"
    assert batch[1].id == "A"
    assert batch[2].id == "C"


def test_ai_enrichment_preserves_lifecycle_timestamps():
    class FakeAI:
        def enrich(self, article):
            return type("Result", (), {"success": True, "title": "AI Title", "content": "AI Body"})()

    service = ProcessingService(source="rss", ai=FakeAI())
    now = datetime.now(UTC)
    art = Article(
        id="A", title="A", url="https://example.com/a", content="Body", source="rss",
        published_at=now - timedelta(minutes=10),
        updated_at=now - timedelta(minutes=5),
        fetched_at=now,
        processed_at=now,
        published_to_channel_at=now,
    )
    enriched = service._enrich(art)
    assert enriched.title == "AI Title"
    assert enriched.content == "AI Body"
    assert enriched.published_at == art.published_at
    assert enriched.updated_at == art.updated_at
    assert enriched.fetched_at == art.fetched_at
    assert enriched.processed_at == art.processed_at
    assert enriched.published_to_channel_at == art.published_to_channel_at


def test_processing_freshness_gate_under_update_policy():
    repos = SQLiteRepositories(":memory:")

    class MockEitaaPublisher(EitaaPublisher):
        def publish(self, article):
            return PublishResult(True, self.name)

    app = YasinPressApplication(repositories=repos, publishers=[MockEitaaPublisher(token="t", channel="c")])
    now = datetime.now(UTC)

    # News published 13 hours ago (stale), but updated 5 minutes ago (fresh!)
    item = FeedItem(
        title="Fresh Update", url="https://example.com/update", content="Body",
        published_at=now - timedelta(hours=13),
        updated_at=now - timedelta(minutes=5)
    )
    report = app.process_items([item])
    # Must be processed and queued!
    assert report.persisted_count == 1
    assert report.processing.old_count == 0
    assert report.processing.queued_count == 1

    repos.close()


def test_normalization_preserves_stored_updated_at():
    repos = SQLiteRepositories(":memory:")

    now = datetime.now(UTC)
    # 1. news item with updated_at T2
    item1 = FeedItem(
        title="News", url="https://example.com/news", content="Body",
        published_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=1)
    )
    art1 = normalize(item1, "source", repository=repos.articles)
    repos.articles.save(art1)

    # 2. same news item without updated_at (incoming updated_at is None)
    item2 = FeedItem(
        title="News", url="https://example.com/news", content="Body",
        published_at=now - timedelta(hours=2),
        updated_at=None
    )
    art2 = normalize(item2, "source", repository=repos.articles)
    # The existing updated_at (now - 1h) must be preserved!
    assert art2.updated_at == now - timedelta(hours=1)

    # 3. same news item with older updated_at (T1 < T2)
    item3 = FeedItem(
        title="News", url="https://example.com/news", content="Body",
        published_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=1, minutes=30)
    )
    art3 = normalize(item3, "source", repository=repos.articles)
    # Stored updated_at must NOT be downgraded/overwritten with older timestamp!
    assert art3.updated_at == now - timedelta(hours=1)

    repos.close()


def test_sqlite_legacy_table_migration():
    # Construct a legacy DB manually with published_at NOT NULL
    db_file = ":memory:"
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            published_at TEXT NOT NULL,
            category TEXT
        )
    """)
    # Insert a legacy record
    conn.execute("""
        INSERT INTO articles (id, title, url, content, source, published_at, category)
        VALUES ('YP-legacy', 'Legacy Title', 'https://example.com/legacy', 'Body', 'rss', '2026-08-11T12:00:00+00:00', 'news')
    """)
    conn.commit()

    # Initialize repository on top of this legacy connection
    repo = ArticleRepository(conn)

    # Verify migration executed and changed published_at column to be nullable
    cursor = conn.execute("PRAGMA table_info(articles)")
    columns = cursor.fetchall()
    published_at_col = next(col for col in columns if col["name"] == "published_at")
    # notnull should be 0 (nullable!)
    assert int(published_at_col["notnull"]) == 0

    # Verify legacy record still exists and can be retrieved
    legacy_art = repo.get("YP-legacy")
    assert legacy_art is not None
    assert legacy_art.title == "Legacy Title"
    assert legacy_art.published_at == datetime(2026, 8, 11, 12, 0, 0, tzinfo=UTC)

    # Verify we can save an article with published_at = None
    new_art = Article(
        id="YP-null-pub", title="Nullable", url="https://example.com/null", content="Body", source="rss",
        published_at=None
    )
    repo.save(new_art)

    retrieved = repo.get("YP-null-pub")
    assert retrieved is not None
    assert retrieved.published_at is None

    conn.close()
