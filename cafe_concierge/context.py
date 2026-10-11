"""Request-scoped guest identity for tools."""

from __future__ import annotations

from contextvars import ContextVar

current_user_sub: ContextVar[str | None] = ContextVar("current_user_sub", default=None)
current_user_name: ContextVar[str] = ContextVar("current_user_name", default="Guest")
current_swiggy_token: ContextVar[str | None] = ContextVar(
    "current_swiggy_token", default=None
)
