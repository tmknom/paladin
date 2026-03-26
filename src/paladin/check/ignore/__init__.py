"""Ignoreパッケージの公開API

ignore ディレクティブの解析・統合・フィルタリング機能を提供する。

Docs:
    - docs/design/ignore.md
"""

from paladin.check.ignore.processor import IgnoreProcessor

__all__ = [
    "IgnoreProcessor",
]
