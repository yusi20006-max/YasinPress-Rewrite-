from __future__ import annotations

from urllib.request import Request, urlopen


def fetch_text(url: str, *, timeout: float = 20.0, user_agent: str = "YasinPress/1.0") -> str:
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8"})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")
