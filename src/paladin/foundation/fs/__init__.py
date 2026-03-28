"""ファイルシステム操作の公開API(Foundation層)。

公開APIは `paladin.foundation.fs` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/internal/fs.md
"""

from paladin.foundation.fs.error import FileSystemError
from paladin.foundation.fs.text import TextFileSystemReader

__all__ = [
    "FileSystemError",
    "TextFileSystemReader",
]
