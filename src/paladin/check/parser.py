"""Check層のAST生成

パイプライン第2段階として、ファイルを読み込みASTに変換する。
"""

import ast
from pathlib import Path

from paladin.check.types import TargetFiles
from paladin.foundation.log import log
from paladin.protocol import TextFileSystemReaderProtocol
from paladin.rule import SourceFile, SourceFiles


class AstParser:
    """ファイルを読み込みAST を生成するパーサー

    読み込み失敗時は FileSystemError がそのまま伝播する。
    構文解析失敗時は SyntaxError をそのまま raise する（Fail Fast 原則）。
    """

    def __init__(self, reader: TextFileSystemReaderProtocol) -> None:
        """AstParserを初期化

        Args:
            reader: ファイル読み込みプロトコル実装
        """
        self.reader = reader

    @log
    def parse(self, file_path: Path) -> SourceFile:
        """単一ファイルを読み込み、ASTを生成する

        Args:
            file_path: 解析対象のファイルパス

        Returns:
            ファイルパスとASTのペア

        Raises:
            FileSystemError: ファイル読み込みエラー時
            SyntaxError: Python構文エラー時
        """
        source = self.reader.read(file_path)
        tree = ast.parse(source)
        return SourceFile(file_path=file_path, tree=tree, source=source)

    @log
    def parse_all(self, target_files: TargetFiles) -> SourceFiles:
        """列挙済み全ファイルを順次AST解析する

        Args:
            target_files: 解析対象ファイル群

        Returns:
            複数ファイルのAST解析結果

        Raises:
            FileSystemError: ファイル読み込みエラー時（Fail Fast）
            SyntaxError: Python構文エラー時（Fail Fast）
        """
        files = tuple(self.parse(file_path) for file_path in target_files)
        return SourceFiles(files=files)
