"""User service layer.

Provides high‑level operations on user entities, delegating to the low‑level
Database class. Keeping this thin wrapper allows future extensions (e.g.
email verification, profile data) without touching handlers.
"""

from core.database import Database


class UserService:
    """Service for user‑related business logic."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get_or_create_user(self, telegram_id: int) -> None:
        """Ensure a user record exists.

        The underlying ``Database.upsert_user`` already performs an INSERT
        with ``ON CONFLICT`` – we simply expose a clearer name.
        """
        self._db.upsert_user(telegram_id)

    def set_language(self, telegram_id: int, language: str) -> None:
        """Set the preferred UI language for a user.

        ``language`` should be ``'ru'`` or ``'en'``; validation is omitted
        because the UI already restricts the options.
        """
        self._db.set_user_language(telegram_id, language)

    def get_language(self, telegram_id: int) -> str:
        """Return stored language, defaulting to ``'ru'`` as defined in DB."""
        return self._db.get_user_language(telegram_id)
