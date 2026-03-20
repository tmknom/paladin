"""インポート文ドメイン値オブジェクト

AST ノードをラップし、インポート文に関する振る舞いをカプセル化する。
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ModulePath:
    """ドット区切りモジュールパスを表す値オブジェクト"""

    value: str  # e.g. "paladin.check.formatter"
    segments: tuple[str, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """初期化時にセグメントを一度だけ計算してキャッシュする"""
        object.__setattr__(self, "segments", tuple(self.value.split(".")))

    @property
    def depth(self) -> int:
        """セグメント数を返す"""
        return len(self.segments)

    @property
    def top_level(self) -> str:
        """先頭セグメント（トップレベルパッケージ名）を返す"""
        return self.segments[0]

    @property
    def package_key(self) -> str:
        """先頭2セグメントを結合したパッケージキーを返す

        セグメント数が2未満の場合はそのまま返す。
        例: "paladin.check.formatter" -> "paladin.check"
             "paladin.check"          -> "paladin.check"
             "paladin"                -> "paladin"
        """
        return ".".join(self.segments[:2])

    def is_subpackage_of(self, parent: "ModulePath") -> bool:
        """Parent 自身またはそのサブパッケージかを判定する"""
        return self.value == parent.value or self.value.startswith(parent.value + ".")

    def __str__(self) -> str:
        """モジュールパス文字列を返す"""
        return self.value


@dataclass(frozen=True)
class ImportedName:
    """インポートされた名前（ast.alias ラッパー）を表す値オブジェクト"""

    name: str  # alias.name
    asname: str | None  # alias.asname

    @property
    def bound_name(self) -> str:
        """バインドされる名前（asname があれば asname、なければ name）を返す"""
        return self.asname if self.asname is not None else self.name

    @property
    def has_alias(self) -> bool:
        """エイリアスが設定されているかを返す"""
        return self.asname is not None

    @staticmethod
    def from_alias(alias: ast.alias) -> "ImportedName":
        """ast.alias から ImportedName を生成する"""
        return ImportedName(name=alias.name, asname=alias.asname)

    @staticmethod
    def from_aliases(aliases: list[ast.alias]) -> tuple["ImportedName", ...]:
        """ast.alias のリストから ImportedName のタプルを生成する"""
        return tuple(ImportedName.from_alias(a) for a in aliases)


@dataclass(frozen=True)
class ImportStatement:
    """インポート文（ast.ImportFrom / ast.Import ラッパー）を表す値オブジェクト"""

    module: ModulePath | None
    names: tuple[ImportedName, ...]
    level: int
    line: int
    column: int
    is_import_from: bool  # True: from X import Y, False: import X

    @property
    def is_relative(self) -> bool:
        """相対インポートかを返す（level >= 1）"""
        return self.level >= 1

    @property
    def is_absolute(self) -> bool:
        """絶対インポートかを返す（level == 0）"""
        return self.level == 0

    @property
    def level_dots(self) -> str:
        """Level 個のドット文字列を返す"""
        return "." * self.level

    @property
    def module_str(self) -> str:
        """モジュールパス文字列を返す（モジュールなしの場合は空文字）"""
        return str(self.module) if self.module is not None else ""

    @property
    def top_level_module(self) -> str | None:
        """モジュールのトップレベル名を返す（module が None の場合は None）"""
        return self.module.top_level if self.module is not None else None

    @property
    def has_module(self) -> bool:
        """モジュールが設定されているかを返す"""
        return self.module is not None

    @staticmethod
    def from_import_from(node: ast.ImportFrom) -> "ImportStatement":
        """ast.ImportFrom から ImportStatement を生成する"""
        module = ModulePath(node.module) if node.module else None
        return ImportStatement(
            module=module,
            names=ImportedName.from_aliases(node.names),
            level=node.level or 0,
            line=node.lineno,
            column=node.col_offset,
            is_import_from=True,
        )

    @staticmethod
    def from_import(node: ast.Import) -> "ImportStatement":
        """ast.Import から ImportStatement を生成する"""
        return ImportStatement(
            module=None,
            names=ImportedName.from_aliases(node.names),
            level=0,
            line=node.lineno,
            column=node.col_offset,
            is_import_from=False,
        )


@dataclass(frozen=True)
class SourceLocation:
    """ソースコード上の位置情報を表す値オブジェクト"""

    file: Path
    line: int
    column: int
