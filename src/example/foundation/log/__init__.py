"""ログ機能の公開API(Foundation層)。

公開APIは `example.foundation.log` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/foundation/log/requirements.md
    - docs/specs/foundation/log/design.md
"""

from example.foundation.log.configurator import LogConfigurator
from example.foundation.log.decorator import log

__all__ = ["LogConfigurator", "log"]
