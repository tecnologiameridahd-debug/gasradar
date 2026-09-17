"""Claves de admin: en Render no se aceptan defaults débiles."""
from __future__ import annotations

import os

WEAK_KEYS = frozenset(
    {
        "gasradar2026",
        "gasradar-alerts-change-me",
        "changeme",
        "change-me",
        "secret",
        "admin",
        "password",
        "gasradar",
    }
)


def on_render() -> bool:
    return bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))


def is_weak_key(value: str | None) -> bool:
    v = (value or "").strip().lower()
    return (not v) or v in WEAK_KEYS


def strip_url_secrets(url: str) -> str:
    """Quita ?key= y fragmentos de una URL de webhook."""
    if not url:
        return ""
    try:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:
        return url.split("?")[0].split("#")[0]
