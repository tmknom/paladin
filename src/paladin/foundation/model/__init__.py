"""データモデル基盤の公開API(Foundation層)。

公開APIは `paladin.foundation.model` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/internal/model.md
"""

from paladin.foundation.model.base import CoreModel
from paladin.foundation.model.settings import CoreSettings, SettingsConfigDict

__all__ = ["CoreModel", "CoreSettings", "SettingsConfigDict"]
