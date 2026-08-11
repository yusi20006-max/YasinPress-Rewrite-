"""Legacy publishing compatibility shim.

The canonical publishing contract lives in :mod:`yasinpress.publishing`.
This module remains import-safe for older integrations while preventing the
legacy ``publish(message) -> bool`` contract from diverging from production.
"""

from yasinpress.publishing import Publisher, PublishResult

__all__ = ["PublishResult", "Publisher"]
