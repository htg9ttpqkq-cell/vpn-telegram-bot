"""Загрузка настроек из переменных окружения (через python-dotenv)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from os import getenv
from typing import Final, NamedTuple, Optional
from urllib.parse import urlparse

from dotenv import find_dotenv, load_dotenv

# Находим файл .env и загружаем его
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# База HTTPS для ссылок вида https://<домен>/<токен> (импорт подписки в клиенте).
DEFAULT_SUBSCRIPTION_CONFIG_BASE_URL: Final[str] = "https://edelia.ru"


def _strip(value: Optional[str]) -> str:
    """Строка из окружения без пробелов по краям; ``None`` → пустая строка."""
    return (value or "").strip()


def _parse_admin_ids(raw_value: Optional[str]) -> tuple[int, ...]:
    """Разбор ``ADMIN_IDS``: список целых через запятую."""
    if not raw_value or not raw_value.strip():
        return ()
    ids: list[int] = []
    for part in raw_value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError as exc:
            raise ValueError(f"Invalid admin ID {part!r} in ADMIN_IDS") from exc
    return tuple(ids)


# Значения из шаблонов .env — не подставлять как реальный хост для ссылок на конфиг.
_PLACEHOLDER_CONFIG_HOSTS: frozenset[str] = frozenset(
    {
        "",
        "vpn.example.com",
        "example.com",
        "www.example.com",
        "example.org",
    }
)


def _normalize_subscription_base(raw: str) -> str:
    """Полный базовый URL без завершающего ``/``."""
    u = raw.strip().rstrip("/")
    if not u.startswith(("http://", "https://")):
        u = "https://" + u.lstrip("/")
    parsed = urlparse(u)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            f"Некорректный URL конфига: {raw!r}. "
            "Задайте SUBSCRIPTION_CONFIG_BASE_URL, например https://edelia.ru"
        )
    return u


def _resolve_vless_template() -> str:
    """Полный URI ``vless://uuid@host:port?...`` для шаблона клиентов."""
    raw = _strip(getenv("VLESS_DOMAIN"))
    if not raw:
        raise ValueError(
            "Задайте VLESS_DOMAIN — полную ссылку vless://... которую бот выдаёт пользователям."
        )
    if not raw.lower().startswith("vless://"):
        raise ValueError(
            f"VLESS_DOMAIN должен начинаться с vless://, получено: {raw[:40]!r}..."
        )
    return raw


def _resolve_subscription_config_base_url() -> str:
    """Приоритет: ``SUBSCRIPTION_CONFIG_BASE_URL`` → ``VLESS_DOMAIN`` (только хост) → значение по умолчанию."""
    explicit = _strip(getenv("SUBSCRIPTION_CONFIG_BASE_URL"))
    if explicit:
        return _normalize_subscription_base(explicit)

    legacy_host = _strip(getenv("VLESS_DOMAIN"))
    if legacy_host:
        host = (
            legacy_host.replace("https://", "")
            .replace("http://", "")
            .split("/")[0]
            .strip()
            .lower()
        )
        if host and host not in _PLACEHOLDER_CONFIG_HOSTS:
            return _normalize_subscription_base(host)

    return DEFAULT_SUBSCRIPTION_CONFIG_BASE_URL


class _YookassaSettings(NamedTuple):
    enabled: bool
    shop_id: str
    secret_key: str
    return_url: str
    webhook_secret: str


def _read_yookassa() -> _YookassaSettings:
    """ЮKassa включена только если заданы и shop id, и secret key."""
    shop_id = _strip(getenv("YOOKASSA_SHOP_ID"))
    secret_key = _strip(getenv("YOOKASSA_SECRET_KEY"))
    return_url = _strip(getenv("YOOKASSA_RETURN_URL")) or "https://t.me"
    webhook_secret = _strip(getenv("YOOKASSA_WEBHOOK_SECRET"))

    has_shop = bool(shop_id)
    has_secret = bool(secret_key)
    if has_shop ^ has_secret:
        raise ValueError(
            "Задайте оба параметра YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY "
            "или оставьте оба пустыми, чтобы отключить ЮKassa."
        )

    if not (has_shop and has_secret):
        return _YookassaSettings(False, "", "", return_url, "")

    return _YookassaSettings(True, shop_id, secret_key, return_url, webhook_secret)


@dataclass(frozen=True)
class Config:
    """Настройки приложения."""

    bot_token: str
    admin_ids: tuple[int, ...]
    db_path: str
    subscription_config_base_url: str
    vless_template: str
    support_text: str
    yookassa_enabled: bool
    yookassa_shop_id: str
    yookassa_secret_key: str
    yookassa_return_url: str
    yookassa_webhook_secret: str
    sbp_recipient: str
    sbp_phone_or_card: str
    delete_user_menu_message_after_sec: int
    welcome_trial_enabled: bool

    @staticmethod
    def _require_env(name: str, value: Optional[str]) -> str:
        raw = _strip(value)
        if not raw:
            raise ValueError(f"Missing required environment variable: {name}")
        return raw

    @classmethod
    def load(cls) -> Config:
        token = cls._require_env("BOT_TOKEN", getenv("BOT_TOKEN"))
        admin_ids = _parse_admin_ids(getenv("ADMIN_IDS"))

        db_path = _strip(getenv("DB_PATH")) or "vpn_bot.db"
        if dotenv_path and not os.path.isabs(db_path):
            env_dir = os.path.dirname(os.path.abspath(dotenv_path))
            db_path = os.path.normpath(os.path.join(env_dir, db_path))
        subscription_config_base_url = _resolve_subscription_config_base_url()
        vless_template = _resolve_vless_template()
        support_raw = _strip(getenv("SUPPORT_TEXT"))
        support_text = support_raw or "Напишите в поддержку: @vpn_support"
        yk = _read_yookassa()
        yookassa_enabled = yk.enabled
        yookassa_shop_id = yk.shop_id
        yookassa_secret_key = yk.secret_key
        yookassa_return_url = yk.return_url
        yookassa_webhook_secret = yk.webhook_secret
        sbp_recipient = _strip(getenv("SBP_RECIPIENT")) or "Котельников Д.А."
        sbp_raw = _strip(getenv("SBP_PHONE_OR_CARD"))
        sbp_phone_or_card = sbp_raw or "+7 933-273-72-87"

        raw_delete_delay = _strip(getenv("DELETE_USER_MENU_MSG_AFTER_SEC"))
        if not raw_delete_delay:
            delete_user_menu_message_after_sec = 45
        else:
            try:
                delete_user_menu_message_after_sec = max(0, int(raw_delete_delay))
            except ValueError:
                delete_user_menu_message_after_sec = 45

        disable_trial = _strip(getenv("DISABLE_WELCOME_TRIAL")).lower()
        welcome_trial_enabled = disable_trial not in ("1", "true", "yes", "on")

        return cls(
            bot_token=token,
            admin_ids=admin_ids,
            db_path=db_path,
            subscription_config_base_url=subscription_config_base_url,
            vless_template=vless_template,
            support_text=support_text,
            yookassa_enabled=yookassa_enabled,
            yookassa_shop_id=yookassa_shop_id,
            yookassa_secret_key=yookassa_secret_key,
            yookassa_return_url=yookassa_return_url,
            yookassa_webhook_secret=yookassa_webhook_secret,
            sbp_recipient=sbp_recipient,
            sbp_phone_or_card=sbp_phone_or_card,
            delete_user_menu_message_after_sec=delete_user_menu_message_after_sec,
            welcome_trial_enabled=welcome_trial_enabled,
        )


PLANS: Final[dict[str, int]] = {
    "trial": 7,
    "1m": 30,
    "3m": 90,
    "12m": 365,
}

PLAN_PRICES_RUB: Final[dict[str, int]] = {
    "1m": 149,
    "3m": 349,
    "12m": 1199,
}

if not frozenset(PLAN_PRICES_RUB) <= frozenset(PLANS):
    raise RuntimeError("Every key in PLAN_PRICES_RUB must exist in PLANS")


def load_config() -> Config:
    """То же, что Config.load() (используется в bot.py и web/webhook.py)."""
    return Config.load()
