"""Single slowapi Limiter instance shared across routers.

Keyed by client IP. slowapi's middleware runs before FastAPI dep resolution,
so the authenticated user isn't available at rate-check time — per-user
limits would require a separate post-auth dep. IP is good enough for the
MVP; tighten later.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
