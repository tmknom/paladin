"""設定管理の公開API。

公開APIは `example.config` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/config/requirements.md
    - docs/specs/config/design.md
"""

from example.config.app import AppConfig
from example.config.env_var import EnvVarConfig

__all__ = [
    "AppConfig",
    "EnvVarConfig",
]
