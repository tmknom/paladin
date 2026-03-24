"""ログ機能の公開API(Foundation層)。

公開APIは `paladin.foundation.log` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/internal/log.md
"""

from paladin.foundation.log.configurator import LogConfigurator
from paladin.foundation.log.decorator import log

__all__ = ["LogConfigurator", "log"]
