"""プロトコル定義の公開API（OnionアーキテクチャのPort定義）。

公開APIは `paladin.protocol` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/internal/protocol.md
"""

from paladin.protocol.fs import TextFileSystemReaderProtocol, TextFileSystemWriterProtocol

__all__ = [
    "TextFileSystemReaderProtocol",
    "TextFileSystemWriterProtocol",
]
