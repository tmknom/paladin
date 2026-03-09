"""設定管理の公開API。

公開APIは `paladin.config` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/config/requirements.md
    - docs/specs/config/design.md
"""

from paladin.config.app import AppConfig
from paladin.config.env_var import EnvVarConfig

__all__ = [
    "AppConfig",
    "EnvVarConfig",
]
