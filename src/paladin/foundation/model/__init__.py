"""データモデル基盤の公開API(Foundation層)。

公開APIは `paladin.foundation.model` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/foundation/model/requirements.md
    - docs/specs/foundation/model/design.md
"""

from paladin.foundation.model.base import CoreModel

__all__ = ["CoreModel"]
