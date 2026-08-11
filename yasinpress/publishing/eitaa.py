from __future__ import annotations

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult


class EitaaPublisher(Publisher):
    """Prepare an Eitaa delivery payload without coupling the domain to HTTP transport."""

    def __init__(self, *, channel: str) -> None:
        self.channel = channel

    @property
    def name(self) -> str:
        return "eitaa"

    def render(self, article: Article) -> str:
        return f"{article.title}\n\n{article.content}\n\n{article.url}"

    def publish(self, article: Article) -> PublishResult:
        self.render(article)
        return PublishResult(True, self.name, external_id=self.channel)
