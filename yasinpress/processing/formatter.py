"""Article presentation formatting."""

from yasinpress.database.models import Article


def format_article(article: Article) -> str:
    """Format an article for publication."""
    category = f"#{article.category}" if article.category else "#news"
    return f"{article.title}\n\n{article.content}\n\n{category}\n{article.url}"
