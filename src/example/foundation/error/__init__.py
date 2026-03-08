"""エラー処理の公開API(Foundation層)。

公開APIは `example.foundation.error` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/foundation/error/requirements.md
    - docs/specs/foundation/error/design.md
"""

from example.foundation.error.error import ApplicationError
from example.foundation.error.handler import ErrorHandler

__all__ = [
    "ApplicationError",
    "ErrorHandler",
]
