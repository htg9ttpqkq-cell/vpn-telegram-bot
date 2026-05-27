"""Загрузка настроек из переменных окружения (через python-dotenv).

Поддерживает мульти-серверную конфигурацию через переменные SERVER_1_*, SERVER_2_*, ...
При их отсутствии — автоматический фоллбек на старые XUI_* переменные (нулевой даунтайм при деплое).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from os import getenv
from typing import Final, List, NamedTuple, Optional
from urllib.parse import urlparse

from dotenv import find_dotenv, load_dotenv

# Находим файл .env и загружаем его
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

import logging

_log = logging.getLogger(__name__)

# База HTTPS для ссылок вида https://<домен>/<токен> (импорт подписки в клиенте).
DEFAULT_SUBSCRIPTION_CONFIG_BASE_URL: Final[str] = "https://edelia.ru"


def _strip(value: Optional[str]) -> str:
    """Строка из окружения без пробелов по краям; ``None`` → пустая строка."""
    return (value or "").strip()


def _parse_admin_ids(raw_value: Optional[str]) -> tuple[int, ...]:
    """Разбор ``ADMIN_IDS``: список целых через запятую, точку с запятой или пробел."""
    if not raw_value or not raw_value.strip():
        return ()
    ids: list[int] = []
    # Заменяем ';' и пробелы на ',' для совместимости
    normalized = raw_value.replace(";", ",").replace(" ", ",")
    for part in normalized.split(","):
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
    """Полный URI ``vless://uuid@host:port?...`` для шаблона клиентов (legacy, single-server)."""
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


class _PlategaSettings(NamedTuple):
    enabled: bool
    merchant_id: str
    secret_key: str
    return_url: str


def _read_platega() -> _PlategaSettings:
    """Platega.io включена только если PLATEGA_ENABLED=True."""
    enabled_str = _strip(getenv("PLATEGA_ENABLED")).lower()
    merchant_id = _strip(getenv("PLATEGA_MERCHANT_ID"))
    secret_key = _strip(getenv("PLATEGA_SECRET_KEY"))
    return_url = _strip(getenv("PLATEGA_RETURN_URL")) or "https://t.me"

    enabled = enabled_str in ("1", "true", "yes", "on")
    if enabled and (not merchant_id or not secret_key):
        raise ValueError(
            "PLATEGA_ENABLED задан как True, но отсутствует PLATEGA_MERCHANT_ID или PLATEGA_SECRET_KEY."
        )
    return _PlategaSettings(enabled, merchant_id, secret_key, return_url)


# ── Multi-server configuration ────────────────────────────────────────────────

@dataclass(frozen=True)
class ServerConfig:
    """Конфигурация одного VPN-сервера (локации).

    Добавление нового сервера — это 1 минута:
    достаточно добавить блок SERVER_N_* в .env без изменения логики кода.
    """

    code: str                   # ISO-код страны, например "DE", "NL"
    display_name: str           # Название с флагом, например "🇩🇪 EDELIA | Germany"
    xui_url: str                # URL 3X-UI панели, например "http://127.0.0.1:2096"
    xui_username: str           # Логин администратора 3X-UI
    xui_password: str           # Пароль администратора 3X-UI
    xui_inbound_id: int         # ID inbound в панели (целое число)
    vless_template: str         # Полная VLESS-ссылка-шаблон (uuid — заглушка)
    subscription_base_url: str  # Базовый URL для ссылок подписки


def _parse_inbound_id(raw: str, fallback: int = 1) -> int:
    """Безопасный парсинг XUI_INBOUND_ID → int."""
    try:
        return int(raw) if raw else fallback
    except ValueError:
        return fallback


def _read_servers(
    fallback_vless_template: str,
    fallback_base_url: str,
) -> list[ServerConfig]:
    """Читает конфигурацию серверов из переменных окружения.

    Стратегия (Strategy A — нулевой даунтайм):
    1. Читаем SERVER_1_*, SERVER_2_*, ... пока CODE не пустой.
    2. Если ни одного SERVER_N_* не задано — читаем старые XUI_* переменные.
    """
    servers: list[ServerConfig] = []
    i = 1
    while True:
        prefix = f"SERVER_{i}_"
        code = _strip(getenv(f"{prefix}CODE"))
        if not code:
            break  # нет SERVER_N_CODE — конец списка
        raw_inbound = _strip(getenv(f"{prefix}XUI_INBOUND_ID"))
        vless_tpl = _strip(getenv(f"{prefix}VLESS_TEMPLATE")) or fallback_vless_template
        base_url_raw = _strip(getenv(f"{prefix}SUBSCRIPTION_BASE_URL"))
        try:
            base_url = _normalize_subscription_base(base_url_raw) if base_url_raw else fallback_base_url
        except ValueError:
            base_url = fallback_base_url
        servers.append(
            ServerConfig(
                code=code,
                display_name=_strip(getenv(f"{prefix}NAME")) or code,
                xui_url=(_strip(getenv(f"{prefix}XUI_URL")) or "http://127.0.0.1:2096").rstrip("/"),
                xui_username=_strip(getenv(f"{prefix}XUI_USERNAME")),
                xui_password=_strip(getenv(f"{prefix}XUI_PASSWORD")),
                xui_inbound_id=_parse_inbound_id(raw_inbound, fallback=1),
                vless_template=vless_tpl,
                subscription_base_url=base_url,
            )
        )
        _log.debug("Loaded server config #%d: %s (%s)", i, code, servers[-1].display_name)
        i += 1

    if not servers:
        # ── Фоллбек на legacy XUI_* переменные ──────────────────────────────
        _log.debug(
            "No SERVER_N_* variables found — falling back to legacy XUI_* variables."
        )
        raw_inbound = _strip(getenv("XUI_INBOUND_ID"))
        servers.append(
            ServerConfig(
                code=_strip(getenv("SERVER_CODE")) or "XX",
                display_name=_strip(getenv("SERVER_NAME")) or "EDELIA | Premium",
                xui_url=(_strip(getenv("XUI_URL")) or "http://127.0.0.1:2096").rstrip("/"),
                xui_username=_strip(getenv("XUI_USERNAME")),
                xui_password=_strip(getenv("XUI_PASSWORD")),
                xui_inbound_id=_parse_inbound_id(raw_inbound, fallback=1),
                vless_template=fallback_vless_template,
                subscription_base_url=fallback_base_url,
            )
        )

    return servers


# ── Main Config dataclass ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Config:
    """Настройки приложения.

    Все старые поля сохранены для обратной совместимости.
    Новые поля: ``servers`` (список локаций), ``uvicorn_host``, ``uvicorn_port``.
    """

    bot_token: str
    admin_ids: tuple[int, ...]
    db_path: str

    # ── Legacy single-server поля (делегируют к servers[0]) ──────────────────
    # Оставлены для нулевого даунтайма — весь старый код работает без изменений.
    subscription_config_base_url: str
    vless_template: str
    xui_url: str
    xui_username: str
    xui_password: str
    xui_inbound_id: int

    # ── Общие настройки ───────────────────────────────────────────────────────
    support_text: str
    yookassa_enabled: bool
    yookassa_shop_id: str
    yookassa_secret_key: str
    yookassa_return_url: str
    yookassa_webhook_secret: str
    platega_enabled: bool
    platega_merchant_id: str
    platega_secret_key: str
    platega_return_url: str
    sbp_recipient: str
    sbp_phone_or_card: str
    delete_user_menu_message_after_sec: int
    welcome_trial_enabled: bool

    # ── Новые поля ────────────────────────────────────────────────────────────
    servers: tuple[ServerConfig, ...]   # Все настроенные серверы
    uvicorn_host: str                   # Хост Uvicorn (default: "127.0.0.1")
    uvicorn_port: int                   # Порт Uvicorn (default: 8000)

    @property
    def primary_server(self) -> ServerConfig:
        """Возвращает первый (основной) сервер."""
        return self.servers[0]

    @staticmethod
    def _require_env(name: str, value: Optional[str]) -> str:
        raw = _strip(value)
        if not raw:
            raise ValueError(f"Missing required environment variable: {name}")
        return raw

    @classmethod
    def load(cls) -> "Config":
        token = cls._require_env("BOT_TOKEN", getenv("BOT_TOKEN"))
        admin_ids = _parse_admin_ids(getenv("ADMIN_IDS"))

        db_path = _strip(getenv("DB_PATH")) or "vpn_bot.db"
        if dotenv_path and not os.path.isabs(db_path):
            env_dir = os.path.dirname(os.path.abspath(dotenv_path))
            db_path = os.path.normpath(os.path.join(env_dir, db_path))

        # Разрешаем базовый URL и vless-шаблон (legacy globals — нужны для фоллбека)
        subscription_config_base_url = _resolve_subscription_config_base_url()
        vless_template = _resolve_vless_template()

        # Читаем серверы (с автофоллбеком на XUI_* если SERVER_1_* не заданы)
        server_list = _read_servers(
            fallback_vless_template=vless_template,
            fallback_base_url=subscription_config_base_url,
        )
        primary = server_list[0]

        support_raw = _strip(getenv("SUPPORT_TEXT"))
        support_text = support_raw or "Напишите в поддержку: @vpn_support"
        yk = _read_yookassa()
        pl = _read_platega()
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

        # Uvicorn host/port (читаем из env, дефолт: 127.0.0.1:8000)
        uvicorn_host = _strip(getenv("UVICORN_HOST")) or "127.0.0.1"
        raw_uvicorn_port = _strip(getenv("UVICORN_PORT"))
        try:
            uvicorn_port = int(raw_uvicorn_port) if raw_uvicorn_port else 8000
        except ValueError:
            uvicorn_port = 8000

        return cls(
            bot_token=token,
            admin_ids=admin_ids,
            db_path=db_path,
            # Legacy single-server поля → берём из primary server
            subscription_config_base_url=primary.subscription_base_url,
            vless_template=primary.vless_template,
            xui_url=primary.xui_url,
            xui_username=primary.xui_username,
            xui_password=primary.xui_password,
            xui_inbound_id=primary.xui_inbound_id,
            # Общие
            support_text=support_text,
            yookassa_enabled=yk.enabled,
            yookassa_shop_id=yk.shop_id,
            yookassa_secret_key=yk.secret_key,
            yookassa_return_url=yk.return_url,
            yookassa_webhook_secret=yk.webhook_secret,
            platega_enabled=pl.enabled,
            platega_merchant_id=pl.merchant_id,
            platega_secret_key=pl.secret_key,
            platega_return_url=pl.return_url,
            sbp_recipient=sbp_recipient,
            sbp_phone_or_card=sbp_phone_or_card,
            delete_user_menu_message_after_sec=delete_user_menu_message_after_sec,
            welcome_trial_enabled=welcome_trial_enabled,
            # Новые поля
            servers=tuple(server_list),
            uvicorn_host=uvicorn_host,
            uvicorn_port=uvicorn_port,
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
