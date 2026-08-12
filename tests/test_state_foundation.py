from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article
from yasinpress.database.sqlite import SQLiteArticleRepository
from yasinpress.processing.freshness import is_fresh
from yasinpress.processing.normalization import normalize
from yasinpress.sources.feed import FeedItem


def test_news_id_format_and_immutability():
    # 1. News ID format: YP-YYMMDD-XXXXXX
    pub_at = datetime(2026, 8, 11, 14, 30, tzinfo=UTC)
    item = FeedItem(
        title="خبر تستی جدید",
        url="https://example.com/unique-news-url",
        content="محتوا",
        published_at=pub_at,
    )
    article = normalize(item, source="test-source", event_id="event-123")

    assert article.id.startswith("YP-260811-")
    assert len(article.id) == 16  # YP- (3) + 260811 (6) + - (1) + XXXXXX (6) = 16 chars
    assert article.event_id == "event-123"
    assert article.lifecycle_state == "fetched"
    assert article.ai_state == "none"


def test_news_id_survives_restart_and_persistence(tmp_path):
    # 2. News ID survives restart (sqlite persistence/repositories)
    db_path = str(tmp_path / "test.db")
    pub_at = datetime(2026, 8, 11, 14, 30, tzinfo=UTC)

    # Save in first repository instance
    repo_first = SQLiteArticleRepository(db_path)
    item = FeedItem(
        title="خبر تستی جدید",
        url="https://example.com/unique-news-url",
        content="محتوا",
        published_at=pub_at,
    )
    article = normalize(item, source="test-source", event_id="event-123")
    news_id = article.id

    repo_first.save(article)
    repo_first.close()

    # Reload in second repository instance (simulates restart)
    repo_second = SQLiteArticleRepository(db_path)
    loaded = repo_second.get(news_id)
    assert loaded is not None
    assert loaded.id == news_id
    assert loaded.event_id == "event-123"
    assert loaded.lifecycle_state == "fetched"

    # Re-normalize same feed item should generate the exact same news ID
    regenerated = normalize(item, source="test-source", event_id="event-123")
    assert regenerated.id == news_id
    repo_second.close()


def test_event_id_grouping_without_conflation():
    # 3. Support Event ID grouping without conflating distinct updates
    # Distinct updates under same event (e.g. different updates have different URLs or dates)
    pub_at1 = datetime(2026, 8, 11, 14, 30, tzinfo=UTC)
    pub_at2 = datetime(2026, 8, 11, 15, 30, tzinfo=UTC)

    item1 = FeedItem(
        title="خبر تستی جدید - آپدیت ۱",
        url="https://example.com/unique-news-url-1",
        content="محتوا ۱",
        published_at=pub_at1,
    )
    item2 = FeedItem(
        title="خبر تستی جدید - آپدیت ۲",
        url="https://example.com/unique-news-url-2",  # Distinct update url
        content="محتوا ۲",
        published_at=pub_at2,
    )

    art1 = normalize(item1, source="test-source", event_id="event-group-1")
    art2 = normalize(item2, source="test-source", event_id="event-group-1")

    assert art1.event_id == art2.event_id == "event-group-1"
    assert art1.id != art2.id  # They have different news IDs because URLs (identities) differ!
    assert art1.id.startswith("YP-260811-")
    assert art2.id.startswith("YP-260811-")


def test_timestamps_and_age_calculation():
    # 4. Persist published/received timestamps and calculate age from publication time
    pub_at = datetime.now(UTC) - timedelta(hours=3)
    item = FeedItem(
        title="خبر",
        url="https://example.com",
        content="محتوا",
        published_at=pub_at,
    )
    article = normalize(item, source="test")

    # Age property should be a timedelta calculated relative to datetime.now(UTC)
    age = article.age
    assert isinstance(age, timedelta)
    # Since it was published 3 hours ago, age should be approximately 3 hours (greater than 0)
    assert age.total_seconds() > 0


def test_freshness_eligibility_scenarios():
    # 5. Normal freshness <=12 hours; breaking/urgent exception explicit and configurable
    now = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)

    # <= 12 hours is fresh
    assert is_fresh(now - timedelta(hours=12), now=now)
    # > 12 hours is NOT fresh
    assert not is_fresh(now - timedelta(hours=12, seconds=1), now=now)

    # Breaking/urgent exception is fresh up to 24h
    assert is_fresh(now - timedelta(hours=23), now=now, is_breaking=True)
    assert is_fresh(now - timedelta(hours=24), now=now, is_breaking=True)
    assert not is_fresh(now - timedelta(hours=24, seconds=1), now=now, is_breaking=True)

    # Custom breaking limit can be configured
    assert is_fresh(
        now - timedelta(hours=47), now=now, is_breaking=True, breaking_max_age=timedelta(hours=48)
    )

    # Breaking exception can be explicitly disabled
    assert not is_fresh(
        now - timedelta(hours=20), now=now, is_breaking=True, allow_breaking_exemption=False
    )


def test_ai_state_and_error_persistence(tmp_path):
    # 6. Persist AI state including rewritten/fallback/failed
    repo = SQLiteArticleRepository(str(tmp_path / "test.db"))

    # Rewritten state
    art_rewritten = Article(
        id="YP-260811-AAAAAA",
        title="عنوان بازنویسی شده",
        url="https://example.com/1",
        content="محتوای بازنویسی شده",
        source="test",
        ai_state="rewritten",
    )
    repo.save(art_rewritten)

    # Fallback state
    art_fallback = Article(
        id="YP-260811-BBBBBB",
        title="عنوان اصلی",
        url="https://example.com/2",
        content="محتوای اصلی",
        source="test",
        ai_state="fallback",
    )
    repo.save(art_fallback)

    # Failed state with error
    art_failed = Article(
        id="YP-260811-CCCCCC",
        title="عنوان اصلی",
        url="https://example.com/3",
        content="محتوای اصلی",
        source="test",
        ai_state="failed",
        ai_error="API limit exceeded",
    )
    repo.save(art_failed)

    # Verify loaded states
    loaded1 = repo.get("YP-260811-AAAAAA")
    assert loaded1.ai_state == "rewritten"
    assert loaded1.ai_error is None

    loaded2 = repo.get("YP-260811-BBBBBB")
    assert loaded2.ai_state == "fallback"
    assert loaded2.ai_error is None

    loaded3 = repo.get("YP-260811-CCCCCC")
    assert loaded3.ai_state == "failed"
    assert loaded3.ai_error == "API limit exceeded"

    repo.close()
