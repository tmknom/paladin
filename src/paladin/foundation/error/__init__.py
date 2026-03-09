"""エラー処理の公開API(Foundation層)。

公開APIは `paladin.foundation.error` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/foundation/error/requirements.md
    - docs/specs/foundation/error/design.md
"""

from paladin.foundation.error.error import ApplicationError
from paladin.foundation.error.handler import ErrorHandler

__all__ = [
    "ApplicationError",
    "ErrorHandler",
]
