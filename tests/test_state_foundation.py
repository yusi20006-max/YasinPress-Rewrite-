from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article
from yasinpress.database.sqlite import SQLiteArticleRepository
from yasinpress.processing.freshness import is_fresh
from yasinpress.processing.normalization import normalize
from yasinpress.sources.feed import FeedItem


def test_news_id_format_and_immutability():
    pub_at = datetime(2026, 8, 11, 14, 30, tzinfo=UTC)
    item = FeedItem(title="خبر تستی جدید", url="https://example.com/unique-news-url", content="محتوا", published_at=pub_at)
    article = normalize(item, source="test-source", event_id="event-123")
    assert article.id.startswith("YP-260811-")
    assert len(article.id) == 16
    assert article.event_id == "event-123"
    assert article.lifecycle_state == "fetched"
    assert article.ai_state == "none"


def test_news_id_survives_restart_and_persistence(tmp_path):
    db_path = str(tmp_path / "test.db")
    pub_at = datetime(2026, 8, 11, 14, 30, tzinfo=UTC)
    repo_first = SQLiteArticleRepository(db_path)
    item = FeedItem(title="خبر تستی جدید", url="https://example.com/unique-news-url", content="محتوا", published_at=pub_at)
    article = normalize(item, source="test-source", event_id="event-123")
    news_id = article.id
    repo_first.save(article)
    repo_first.close()
    repo_second = SQLiteArticleRepository(db_path)
    loaded = repo_second.get(news_id)
    assert loaded is not None
    assert loaded.id == news_id
    assert loaded.event_id == "event-123"
    assert loaded.lifecycle_state == "fetched"
    regenerated = normalize(item, source="test-source", event_id="event-123")
    assert regenerated.id == news_id
    repo_second.close()


def test_event_id_grouping_without_conflation():
    pub_at1 = datetime(2026, 8, 11, 14, 30, tzinfo=UTC)
    pub_at2 = datetime(2026, 8, 11, 15, 30, tzinfo=UTC)
    item1 = FeedItem(title="خبر تستی جدید - آپدیت ۱", url="https://example.com/unique-news-url-1", content="محتوا ۱", published_at=pub_at1)
    item2 = FeedItem(title="خبر تستی جدید - آپدیت ۲", url="https://example.com/unique-news-url-2", content="محتوا ۲", published_at=pub_at2)
    art1 = normalize(item1, source="test-source", event_id="event-group-1")
    art2 = normalize(item2, source="test-source", event_id="event-group-1")
    assert art1.event_id == art2.event_id == "event-group-1"
    assert art1.id != art2.id
    assert art1.id.startswith("YP-260811-")
    assert art2.id.startswith("YP-260811-")


def test_timestamps_and_age_calculation():
    pub_at = datetime.now(UTC) - timedelta(hours=3)
    item = FeedItem(title="خبر", url="https://example.com", content="محتوا", published_at=pub_at)
    article = normalize(item, source="test")
    age = article.age
    assert isinstance(age, timedelta)
    assert age.total_seconds() > 0


def test_freshness_eligibility_scenarios():
    # Production contract: every article, including breaking news, is limited to 12h.
    now = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    assert is_fresh(now - timedelta(hours=12), now=now)
    assert not is_fresh(now - timedelta(hours=12, seconds=1), now=now)
    assert is_fresh(now - timedelta(hours=12), now=now, is_breaking=True)
    assert not is_fresh(now - timedelta(hours=12, seconds=1), now=now, is_breaking=True)
    assert not is_fresh(now - timedelta(hours=20), now=now, is_breaking=True, allow_breaking_exemption=False)


def test_ai_state_and_error_persistence(tmp_path):
    repo = SQLiteArticleRepository(str(tmp_path / "test.db"))
    art_rewritten = Article(id="YP-260811-AAAAAA", title="عنوان بازنویسی شده", url="https://example.com/1", content="محتوای بازنویسی شده", source="test", ai_state="rewritten")
    repo.save(art_rewritten)
    art_fallback = Article(id="YP-260811-BBBBBB", title="عنوان اصلی", url="https://example.com/2", content="محتوای اصلی", source="test", ai_state="fallback")
    repo.save(art_fallback)
    art_failed = Article(id="YP-260811-CCCCCC", title="عنوان اصلی", url="https://example.com/3", content="محتوای اصلی", source="test", ai_state="failed", ai_error="API limit exceeded")
    repo.save(art_failed)
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
