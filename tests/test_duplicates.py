from dataclasses import dataclass

from yasinpress.database.models import Article
from yasinpress.processing.duplicates import DuplicateDetector


@dataclass
class FakeRepository:
    ids: set[str]

    def exists(self, article_id: str) -> bool:
        return article_id in self.ids


def test_exact_duplicate_uses_repository_id():
    detector = DuplicateDetector(FakeRepository({"known"}))
    article = Article(
        id="known", title="News", url="https://example.com", content="body", source="rss"
    )
    assert detector.is_duplicate(article)


def test_title_similarity_detects_near_duplicate():
    detector = DuplicateDetector(FakeRepository(set()), threshold=0.85)
    result = detector.compare_title("Major news update today", ["Major news update today!"])
    assert result.is_duplicate
    assert result.matched_index == 0


def test_title_similarity_rejects_dissimilar_title():
    detector = DuplicateDetector(FakeRepository(set()), threshold=0.85)
    result = detector.compare_title("Technology market update", ["Local football match results"])
    assert not result.is_duplicate


def test_empty_title_is_not_duplicate():
    detector = DuplicateDetector(FakeRepository(set()))
    result = detector.compare_title("   ", ["Existing article"])
    assert not result.is_duplicate
    assert result.score == 0.0


def test_invalid_threshold_is_rejected():
    try:
        DuplicateDetector(FakeRepository(set()), threshold=1.1)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid threshold must raise ValueError")
