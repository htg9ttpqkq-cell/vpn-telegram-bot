"""VLESS-конфиг из переменной окружения ``VLESS_DOMAIN``."""

from __future__ import annotations


def vless_link_from_env(vless_domain: str) -> str:
    link = vless_domain.strip()
    if not link.lower().startswith("vless://"):
        raise ValueError("VLESS_DOMAIN must be a full vless:// URI")
    return link
