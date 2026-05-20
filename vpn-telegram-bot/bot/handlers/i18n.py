"""Shared localization helpers for handlers."""

from __future__ import annotations

from functools import lru_cache
from typing import FrozenSet

from . import ui_texts


def normalize_lang(lang: str) -> str:
    return "en" if lang == "en" else "ru"


def t(lang: str, key: str) -> str:
    return ui_texts.texts[normalize_lang(lang)][key]


def plan_title(lang: str, code: str) -> str:
    return ui_texts.plan_titles[normalize_lang(lang)].get(code, "—")


def plan_duration(lang: str, code: str) -> str:
    return ui_texts.plan_durations[normalize_lang(lang)].get(code, "—")


@lru_cache(maxsize=None)
def all_locale_values(key: str) -> FrozenSet[str]:
    """Every localized string for `key` (for matching reply keyboard text)."""
    return frozenset(
        {
            ui_texts.texts["ru"][key],
            ui_texts.texts["en"][key],
        }
    )
