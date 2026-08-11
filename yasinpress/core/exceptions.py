"""Domain specific exceptions for YasinPress."""


class YasinPressError(Exception):
    """Base exception for recoverable application failures."""


class ConfigurationError(YasinPressError):
    """Raised when configuration cannot be loaded or validated."""


class RepositoryError(YasinPressError):
    """Raised when persistence operations fail."""


class PublishError(YasinPressError):
    """Raised when a publisher cannot deliver content."""
