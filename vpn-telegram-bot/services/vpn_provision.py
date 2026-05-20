"""Выдача VLESS-конфига пользователю."""

from __future__ import annotations

from core.config import Config
from core.database import UserSubscription


def generate_vless_link(template: str, client_uuid: str) -> str:
    """Генерирует персональную VLESS-ссылку на основе шаблона и UUID клиента."""
    if not template.startswith("vless://"):
        return template
    parts = template.split("@", 1)
    if len(parts) < 2:
        return template
    return f"vless://{client_uuid}@{parts[1]}"


def vless_config_link(config: Config) -> str:
    """Прямая ссылка ``vless://...`` из ``VLESS_DOMAIN``."""
    return config.vless_template


def needs_config_refresh(subscription: UserSubscription | None, config: Config) -> bool:
    if subscription is None:
        return True
    if not subscription.client_uuid:
        return True
    expected = generate_vless_link(config.vless_template, subscription.client_uuid)
    return (subscription.vless_link or "").strip() != expected.strip()

