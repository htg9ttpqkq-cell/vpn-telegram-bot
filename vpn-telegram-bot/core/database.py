"""Слой доступа к базе данных (SQLite).

Ключевые гарантии:
  - Все модификации выполняются под self._lock (thread-safe).
  - Атомарные операции (активация + реферал) используют явные SQLite-транзакции
    с BEGIN / COMMIT / ROLLBACK, исключая частичное применение.
  - Защита от Race Condition при подтверждении платежей через
    UPDATE … WHERE status = 'pending_review' с проверкой rowcount.
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, Iterator, List, Optional, Set, Tuple


@dataclass
class UserSubscription:
    user_id: int
    plan: Optional[str]
    expires_at: Optional[datetime]
    is_active: bool
    vless_link: Optional[str]
    sub_token: Optional[str] = None
    client_uuid: Optional[str] = None


@dataclass
class PaymentRecord:
    id: int
    user_id: int
    plan: str
    amount: int
    status: str
    yookassa_payment_id: Optional[str]
    platega_transaction_id: Optional[str]
    comment: Optional[str]


class Database:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._lock = Lock()

    # ── Соединение ────────────────────────────────────────────────────────────

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Открывает соединение с автоматическим commit/close."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        # Включаем WAL-режим для конкурентного чтения без блокировок
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    @contextmanager
    def _transact(self) -> Iterator[sqlite3.Connection]:
        """Открывает соединение с явной транзакцией (BEGIN IMMEDIATE / ROLLBACK).

        Используйте для атомарных составных операций, где нужен rollback.
        IMMEDIATE блокирует запись сразу, исключая конкурентные UPDATE-ы.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.isolation_level = None  # ручное управление транзакцией
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    # ── Инициализация схемы ───────────────────────────────────────────────────

    def init(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT NOT NULL DEFAULT 'ru',
                    trial_consumed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    plan TEXT,
                    expires_at TEXT,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    vless_link TEXT UNIQUE,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    yookassa_payment_id TEXT UNIQUE,
                    idempotency_key TEXT UNIQUE,
                    comment TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS referrals (
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL PRIMARY KEY,
                    rewarded INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(referred_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            # Индекс для быстрого поиска просроченных подписок (фоновый планировщик)
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_subs_active_expires
                ON subscriptions (is_active, expires_at)
                """
            )
            self._migrate_existing_schema(conn)

    def _migrate_existing_schema(self, conn: sqlite3.Connection) -> None:
        user_columns: Set[str] = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "language" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'ru'")
        if "trial_consumed" not in user_columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN trial_consumed INTEGER NOT NULL DEFAULT 0"
            )

        columns: Set[str] = {
            row["name"] for row in conn.execute("PRAGMA table_info(subscriptions)").fetchall()
        }
        if "plan" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN plan TEXT")
        if "expires_at" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN expires_at TEXT")
        if "subscription_end" in columns:
            conn.execute(
                "UPDATE subscriptions SET expires_at = subscription_end WHERE expires_at IS NULL"
            )
        if "vless_link" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN vless_link TEXT")
        if "vpn_link" in columns:
            conn.execute("UPDATE subscriptions SET vless_link = vpn_link WHERE vless_link IS NULL")
        if "sub_token" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN sub_token TEXT")
        if "client_uuid" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN client_uuid TEXT")

        payment_columns: Set[str] = {
            row["name"] for row in conn.execute("PRAGMA table_info(payments)").fetchall()
        }
        if "comment" not in payment_columns:
            conn.execute("ALTER TABLE payments ADD COLUMN comment TEXT")
        if "platega_transaction_id" not in payment_columns:
            conn.execute("ALTER TABLE payments ADD COLUMN platega_transaction_id TEXT")

    # ── Users ─────────────────────────────────────────────────────────────────

    def upsert_user(self, user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, language, created_at, updated_at)
                VALUES (?, 'ru', ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (user_id, now, now),
            )
            conn.execute(
                """
                INSERT INTO subscriptions (user_id, is_active, updated_at)
                VALUES (?, 0, ?)
                ON CONFLICT(user_id) DO NOTHING
                """,
                (user_id, now),
            )

    def user_trial_consumed(self, user_id: int) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT trial_consumed FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return False
        return bool(row["trial_consumed"])

    def set_trial_consumed(self, user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE users SET trial_consumed = 1, updated_at = ? WHERE user_id = ?",
                (now, user_id),
            )

    def get_user_language(self, user_id: int) -> str:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT language FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None or not row["language"]:
            return "ru"
        return str(row["language"])

    def set_user_language(self, user_id: int, language: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, language, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    language = excluded.language,
                    updated_at = excluded.updated_at
                """,
                (user_id, language, now, now),
            )

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def _row_to_subscription(self, row: sqlite3.Row) -> UserSubscription:
        raw_expires = row["expires_at"]
        if raw_expires:
            expires_at = datetime.fromisoformat(raw_expires)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = None
        keys = row.keys()
        return UserSubscription(
            user_id=row["user_id"],
            plan=row["plan"],
            expires_at=expires_at,
            is_active=bool(row["is_active"]),
            vless_link=row["vless_link"],
            sub_token=row["sub_token"] if "sub_token" in keys else None,
            client_uuid=row["client_uuid"] if "client_uuid" in keys else None,
        )

    def get_subscription(self, user_id: int) -> Optional[UserSubscription]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, plan, expires_at, is_active, vless_link, sub_token, client_uuid
                FROM subscriptions WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_subscription(row)

    def get_subscription_by_token(self, sub_token: str) -> Optional[UserSubscription]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, plan, expires_at, is_active, vless_link, sub_token, client_uuid
                FROM subscriptions WHERE sub_token = ?
                """,
                (sub_token,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_subscription(row)

    def get_subscription_by_link_suffix(self, token: str) -> Optional[UserSubscription]:
        """Legacy-ссылки ``https://host/<token>`` без ``/sub/``."""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, plan, expires_at, is_active, vless_link, sub_token, client_uuid
                FROM subscriptions WHERE vless_link LIKE ? LIMIT 1
                """,
                (f"%/{token}",),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_subscription(row)

    def set_subscription(
        self,
        user_id: int,
        *,
        plan: str,
        expires_at: datetime,
        is_active: bool,
        vless_link: str,
        sub_token: Optional[str] = None,
        client_uuid: Optional[str] = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO subscriptions (
                    user_id, plan, expires_at, is_active, vless_link,
                    sub_token, client_uuid, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    plan       = excluded.plan,
                    expires_at = excluded.expires_at,
                    is_active  = excluded.is_active,
                    vless_link = excluded.vless_link,
                    sub_token  = excluded.sub_token,
                    client_uuid = excluded.client_uuid,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id, plan, expires_at.isoformat(), int(is_active),
                    vless_link, sub_token, client_uuid, now,
                ),
            )

    def activate_subscription_with_referral(
        self,
        *,
        user_id: int,
        plan: str,
        expires_at: datetime,
        vless_link: str,
        sub_token: str,
        client_uuid: str,
        referrer_id: Optional[int],
    ) -> None:
        """Активирует подписку и (опционально) начисляет реферальный бонус —
        в рамках единой ACID-транзакции.

        Если любой шаг выбрасывает исключение — вся транзакция откатывается.
        Это исключает ситуацию «реферал начислен, но подписка не сохранена».
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._transact() as conn:
            # 1. Активируем подписку
            conn.execute(
                """
                INSERT INTO subscriptions (
                    user_id, plan, expires_at, is_active, vless_link,
                    sub_token, client_uuid, updated_at
                )
                VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    plan        = excluded.plan,
                    expires_at  = excluded.expires_at,
                    is_active   = 1,
                    vless_link  = excluded.vless_link,
                    sub_token   = excluded.sub_token,
                    client_uuid = excluded.client_uuid,
                    updated_at  = excluded.updated_at
                """,
                (user_id, plan, expires_at.isoformat(), vless_link, sub_token, client_uuid, now),
            )
            # 2. Отмечаем триал использованным
            conn.execute(
                "UPDATE users SET trial_consumed = 1, updated_at = ? WHERE user_id = ?",
                (now, user_id),
            )
            # 3. Реферальное вознаграждение (только если реферер задан)
            if referrer_id is not None:
                conn.execute(
                    """
                    UPDATE referrals SET rewarded = 1
                    WHERE referrer_id = ? AND referred_id = ? AND rewarded = 0
                    """,
                    (referrer_id, user_id),
                )

    def deactivate_subscription(self, user_id: int) -> None:
        """Принудительно деактивирует подписку (вызывается фоновым планировщиком)."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE subscriptions SET is_active = 0, updated_at = ? WHERE user_id = ?",
                (now, user_id),
            )

    def get_expired_active_subscriptions(self) -> List[UserSubscription]:
        """Возвращает все активные подписки с истёкшим сроком (для фонового cron)."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT user_id, plan, expires_at, is_active, vless_link, sub_token, client_uuid
                FROM subscriptions
                WHERE is_active = 1 AND expires_at IS NOT NULL AND expires_at <= ?
                """,
                (now,),
            ).fetchall()
        return [self._row_to_subscription(r) for r in rows]

    def reset_vless_link(
        self,
        user_id: int,
        new_link: str,
        *,
        sub_token: Optional[str] = None,
        client_uuid: Optional[str] = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE subscriptions
                SET vless_link = ?, sub_token = ?, client_uuid = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (new_link, sub_token, client_uuid, now, user_id),
            )

    def clear_subscription(self, user_id: int) -> None:
        """Сброс подписки: неактивна, без плана, срока и конфига."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE subscriptions
                SET plan = NULL, expires_at = NULL, is_active = 0,
                    vless_link = NULL, sub_token = NULL, client_uuid = NULL,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (now, user_id),
            )

    # ── Payments ──────────────────────────────────────────────────────────────

    def create_payment(
        self,
        *,
        user_id: int,
        plan: str,
        amount: int,
        status: str,
        yookassa_payment_id: Optional[str] = None,
        platega_transaction_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO payments (
                    user_id, plan, amount, status, yookassa_payment_id,
                    platega_transaction_id, idempotency_key, comment, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(yookassa_payment_id) DO UPDATE SET
                    status     = excluded.status,
                    comment    = excluded.comment,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id, plan, amount, status,
                    yookassa_payment_id, platega_transaction_id, idempotency_key, comment, now, now,
                ),
            )
            return int(cursor.lastrowid)

    def claim_payment_atomic(self, payment_id: int) -> bool:
        """Атомарно захватывает платёж: меняет статус с 'pending_review' → 'processing'.

        Возвращает True только если строка была изменена (первый вызов).
        Параллельные вызовы вернут False — защита от Double-Spending.
        Использует BEGIN IMMEDIATE для исключения гонки записи.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._transact() as conn:
            cursor = conn.execute(
                """
                UPDATE payments SET status = 'processing', updated_at = ?
                WHERE id = ? AND status = 'pending_review'
                """,
                (now, payment_id),
            )
            return cursor.rowcount == 1

    def claim_yookassa_payment_atomic(self, yookassa_payment_id: str) -> bool:
        """Аналог claim_payment_atomic для YooKassa-вебхуков.

        Защита от повторной обработки одного и того же payment_id.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._transact() as conn:
            cursor = conn.execute(
                """
                UPDATE payments SET status = 'processing', updated_at = ?
                WHERE yookassa_payment_id = ? AND status NOT IN ('paid', 'processing')
                """,
                (now, yookassa_payment_id),
            )
            return cursor.rowcount == 1

    def claim_platega_payment_atomic(self, platega_transaction_id: str) -> bool:
        """Аналог claim_yookassa_payment_atomic для Platega-вебхуков.

        Защита от повторной обработки одного и того же transaction_id.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._transact() as conn:
            cursor = conn.execute(
                """
                UPDATE payments SET status = 'processing', updated_at = ?
                WHERE platega_transaction_id = ? AND status NOT IN ('paid', 'processing')
                """,
                (now, platega_transaction_id),
            )
            return cursor.rowcount == 1

    def get_payment_by_yookassa_id(self, yookassa_payment_id: str) -> Optional[PaymentRecord]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, plan, amount, status, yookassa_payment_id, platega_transaction_id, comment
                FROM payments WHERE yookassa_payment_id = ?
                """,
                (yookassa_payment_id,),
            ).fetchone()
        if row is None:
            return None
        return PaymentRecord(
            id=row["id"],
            user_id=row["user_id"],
            plan=row["plan"],
            amount=row["amount"],
            status=row["status"],
            yookassa_payment_id=row["yookassa_payment_id"],
            platega_transaction_id=row["platega_transaction_id"],
            comment=row["comment"],
        )

    def get_payment_by_platega_id(self, platega_transaction_id: str) -> Optional[PaymentRecord]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, plan, amount, status, yookassa_payment_id, platega_transaction_id, comment
                FROM payments WHERE platega_transaction_id = ?
                """,
                (platega_transaction_id,),
            ).fetchone()
        if row is None:
            return None
        return PaymentRecord(
            id=row["id"],
            user_id=row["user_id"],
            plan=row["plan"],
            amount=row["amount"],
            status=row["status"],
            yookassa_payment_id=row["yookassa_payment_id"],
            platega_transaction_id=row["platega_transaction_id"],
            comment=row["comment"],
        )

    def get_payment_by_id(self, payment_id: int) -> Optional[PaymentRecord]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, plan, amount, status, yookassa_payment_id, platega_transaction_id, comment
                FROM payments WHERE id = ?
                """,
                (payment_id,),
            ).fetchone()
        if row is None:
            return None
        return PaymentRecord(
            id=row["id"],
            user_id=row["user_id"],
            plan=row["plan"],
            amount=row["amount"],
            status=row["status"],
            yookassa_payment_id=row["yookassa_payment_id"],
            platega_transaction_id=row["platega_transaction_id"],
            comment=row["comment"],
        )

    def update_payment_status(self, yookassa_payment_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE payments SET status = ?, updated_at = ? WHERE yookassa_payment_id = ?",
                (status, now, yookassa_payment_id),
            )

    def update_payment_status_by_platega_id(self, platega_transaction_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE payments SET status = ?, updated_at = ? WHERE platega_transaction_id = ?",
                (status, now, platega_transaction_id),
            )

    def update_payment_status_by_id(self, payment_id: int, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE payments SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, payment_id),
            )

    def list_pending_payments(self, limit: int = 50) -> List[PaymentRecord]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, plan, amount, status, yookassa_payment_id, platega_transaction_id, comment
                FROM payments WHERE status = 'pending_review'
                ORDER BY created_at ASC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            PaymentRecord(
                id=r["id"], user_id=r["user_id"], plan=r["plan"], amount=r["amount"],
                status=r["status"], yookassa_payment_id=r["yookassa_payment_id"],
                platega_transaction_id=r["platega_transaction_id"], comment=r["comment"],
            )
            for r in rows
        ]

    def list_users(self, limit: int = 100) -> List[UserSubscription]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT user_id, plan, expires_at, is_active, vless_link
                FROM subscriptions ORDER BY updated_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        result: List[UserSubscription] = []
        for row in rows:
            raw_expires = row["expires_at"]
            result.append(
                UserSubscription(
                    user_id=row["user_id"],
                    plan=row["plan"],
                    expires_at=datetime.fromisoformat(raw_expires) if raw_expires else None,
                    is_active=bool(row["is_active"]),
                    vless_link=row["vless_link"],
                )
            )
        return result

    # ── Referrals ─────────────────────────────────────────────────────────────

    def set_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Сохраняет реферальную связь. Возвращает True если связь создана впервые."""
        if referrer_id == referred_id:
            return False
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT referrer_id FROM referrals WHERE referred_id = ?",
                (referred_id,),
            ).fetchone()
            if existing:
                return False
            conn.execute(
                """
                INSERT OR IGNORE INTO referrals (referrer_id, referred_id, rewarded, created_at)
                VALUES (?, ?, 0, ?)
                """,
                (referrer_id, referred_id, now),
            )
        return True

    def get_referrer(self, referred_id: int) -> Optional[int]:
        """Возвращает user_id реферера для данного пользователя (только если ещё не вознаграждён)."""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT referrer_id FROM referrals WHERE referred_id = ? AND rewarded = 0",
                (referred_id,),
            ).fetchone()
        return int(row["referrer_id"]) if row else None

    def mark_referral_rewarded(self, referrer_id: int, referred_id: int) -> None:
        """Помечает реферальное вознаграждение как выданное."""
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE referrals SET rewarded = 1 WHERE referrer_id = ? AND referred_id = ?",
                (referrer_id, referred_id),
            )

    def get_referral_stats(self, user_id: int) -> Tuple[int, int]:
        """Возвращает (всего_приглашено, вознаграждений_получено)."""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total, SUM(rewarded) AS rewarded
                FROM referrals WHERE referrer_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return (0, 0)
        return (int(row["total"]), int(row["rewarded"] or 0))

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_bot_stats(self) -> Dict[str, int]:
        """Возвращает агрегированную статистику бота."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        with self._lock, self._connect() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active_subs = conn.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE is_active = 1 AND expires_at > ?",
                (now.isoformat(),),
            ).fetchone()[0]
            trials_today = conn.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE plan = 'trial' AND updated_at >= ?",
                (today_start,),
            ).fetchone()[0]
            total_referral_rewards = conn.execute(
                "SELECT COUNT(*) FROM referrals WHERE rewarded = 1"
            ).fetchone()[0]
        return {
            "total_users": int(total_users),
            "active_subs": int(active_subs),
            "trials_today": int(trials_today),
            "total_referral_rewards": int(total_referral_rewards),
        }
