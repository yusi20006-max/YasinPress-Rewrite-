"""API authentication."""
import hmac

class TokenAuth:
    """Constant-time bearer token validator."""
    def __init__(self, token: str) -> None:
        self.token = token
    def verify(self, supplied: str) -> bool:
        """Verify a supplied token."""
        return hmac.compare_digest(self.token, supplied)
