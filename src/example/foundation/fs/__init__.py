"""ファイルシステム操作の公開API(Foundation層)。

公開APIは `example.foundation.fs` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/foundation/fs/requirements.md
    - docs/specs/foundation/fs/design.md
"""

from example.foundation.fs.error import FileSystemError
from example.foundation.fs.text import TextFileSystemReader, TextFileSystemWriter

__all__ = [
    "FileSystemError",
    "TextFileSystemReader",
    "TextFileSystemWriter",
]
