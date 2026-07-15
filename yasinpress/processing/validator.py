"""Article validation."""
from yasinpress.database.models import Article


def validate_article(article: Article) -> None:
    """Validate required article fields."""
    if not article.title or not article.url.startswith(("http://", "https://")):
        raise ValueError("Article requires a title and absolute URL")
