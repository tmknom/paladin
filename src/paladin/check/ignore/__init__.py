"""ファイル単位・行単位の Ignore 機能の公開 API。

公開 API は `paladin.check.ignore` から import すること。

Docs:
    - docs/design/ignore.md
"""

from paladin.check.ignore.processor import IgnoreProcessor

__all__ = [
    "IgnoreProcessor",
]
