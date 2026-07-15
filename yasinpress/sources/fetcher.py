"""HTTP feed fetching."""
import httpx

class FetchEngine:
    """Fetches remote feed documents."""
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch(self, url: str) -> str:
        """Fetch a URL and return response text."""
        response = httpx.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text
