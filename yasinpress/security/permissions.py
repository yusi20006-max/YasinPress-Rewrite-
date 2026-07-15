"""Permission checks."""

def has_permission(user_permissions: set[str], required: str) -> bool:
    """Return whether a permission is granted."""
    return required in user_permissions or "admin" in user_permissions
