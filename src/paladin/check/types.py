"""Check層のドメインモデル定義

パイプライン各段階の入出力を表す値オブジェクトと出力形式の列挙型を定義する。
"""

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


@dataclass(frozen=True)
class TargetFiles:
    """列挙された解析対象ファイル群を保持する不変な値オブジェクト

    Constraints:
        - インスタンス生成後は変更不可（frozen=True）
        - files は重複排除・ソート済みであることを前提とする
    """

    files: tuple[Path, ...]
    """重複排除・ソート済みの .py ファイルパス群"""

    def __len__(self) -> int:
        """ファイル数を返す"""
        return len(self.files)

    def __iter__(self) -> Iterator[Path]:
        """ファイルパスをイテレーションする"""
        return iter(self.files)


@dataclass(frozen=True)
class ParsedFile:
    """単一ファイルのAST解析結果を保持する不変な値オブジェクト"""

    file_path: Path
    tree: ast.Module


@dataclass(frozen=True)
class ParsedFiles:
    """複数ファイルのAST解析結果を集約する不変な値オブジェクト"""

    files: tuple[ParsedFile, ...]

    def __len__(self) -> int:
        """解析済みファイル数を返す"""
        return len(self.files)

    def __iter__(self) -> Iterator[ParsedFile]:
        """解析済みファイルをイテレーションする"""
        return iter(self.files)


class OutputFormat(Enum):
    """チェック結果の出力フォーマット"""

    TEXT = "text"
    JSON = "json"
