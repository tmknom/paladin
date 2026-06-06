"""Rule 層の静的解析ルール。許可ディレクトリ外でのサードパーティインポート禁止ルール。

仕様は docs/rules/no-third-party-import.md を参照。
"""

import sys
from pathlib import Path

from paladin.rule.import_statement import ImportStatement, ModulePath
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import DetectionContext, RuleMeta, SourceFile, SourceFiles, Violation


class ThirdPartyChecker:
    """サードパーティライブラリかどうかの判定を行う"""

    @staticmethod
    def is_third_party(
        module_name: str,
        stdlib_modules: frozenset[str],
        root_packages: tuple[str, ...],
    ) -> bool:
        """標準ライブラリとルートパッケージを除いたサードパーティかを判定する"""
        if module_name in stdlib_modules:
            return False
        return module_name not in root_packages

    @staticmethod
    def is_allowed_path(file_path: Path, allow_dirs: tuple[str, ...]) -> bool:
        """ファイルパスが allow_dirs のいずれかに前方一致するかを判定する"""
        try:
            rel_str = str(file_path.relative_to(Path.cwd()))
        except ValueError:
            rel_str = str(file_path)
        return any(rel_str.startswith(allow_dir) for allow_dir in allow_dirs)

    @staticmethod
    def is_allow_file(file_path: Path, allow_files: frozenset[str]) -> bool:
        """ファイルパスが allow_files に完全一致するかを判定する"""
        try:
            rel_str = str(file_path.relative_to(Path.cwd()))
        except ValueError:
            rel_str = str(file_path)
        return rel_str in allow_files


class ThirdPartyImportDetector:
    """サードパーティインポートの Violation を生成する"""

    @staticmethod
    def detect_from_import(
        ctx: DetectionContext,
        stmt: ImportStatement,
    ) -> list[Violation]:
        """From X import Y 形式の違反リストを返す"""
        module_str = stmt.module_str
        violations: list[Violation] = []
        for imported in stmt.names:
            violations.append(
                ctx.meta.create_violation_at(
                    location=ctx.source_file.location_from(stmt),
                    message=f"`from {module_str} import {imported.name}` は許可ディレクトリ外でのサードパーティライブラリのインポートである",
                    reason="サードパーティライブラリの利用は `allow-dirs` で指定されたディレクトリに集約する必要がある",
                    suggestion=f"`{module_str}` の利用を許可ディレクトリ配下に移動するか、ラッパーモジュール経由でアクセスしてください",
                )
            )
        return violations

    @staticmethod
    def detect_plain_import(
        ctx: DetectionContext,
        stmt: ImportStatement,
        imported_name: str,
    ) -> Violation:
        """Import X 形式の違反を返す"""
        return ctx.meta.create_violation_at(
            location=ctx.source_file.location_from(stmt),
            message=f"`import {imported_name}` は許可ディレクトリ外でのサードパーティライブラリのインポートである",
            reason="サードパーティライブラリの利用は `allow-dirs` で指定されたディレクトリに集約する必要がある",
            suggestion=f"`{imported_name}` の利用を許可ディレクトリ配下に移動するか、ラッパーモジュール経由でアクセスしてください",
        )


class NoThirdPartyImportRule:
    """許可ディレクトリ以外でのサードパーティライブラリのインポートを検出するルール"""

    def __init__(self, allow_dirs: tuple[str, ...] = (), allow_files: tuple[str, ...] = ()) -> None:
        """ルールを初期化する

        Args:
            allow_dirs: サードパーティインポートを許可するディレクトリのパス
            allow_files: サードパーティインポート検査を除外するファイルのパス
        """
        self._allow_dirs = tuple(d if d.endswith("/") else d + "/" for d in allow_dirs)
        self._allow_files = frozenset(allow_files)
        self._resolver = PackageResolver()
        self._root_packages: tuple[str, ...] = ()
        self._stdlib_modules: frozenset[str] = sys.stdlib_module_names
        self._meta = RuleMeta(
            rule_id="no-third-party-import",
            rule_name="No Third Party Import",
            summary="許可ディレクトリ以外でのサードパーティライブラリのインポートを禁止する",
            intent="サードパーティライブラリの利用を特定ディレクトリに集約し、外部依存の境界を明確にする",
            guidance="allow-dirs 外でサードパーティライブラリをインポートしている箇所を確認する",
            suggestion="サードパーティライブラリの利用を allow-dirs で指定されたディレクトリに移動するか、ラッパーモジュール経由でアクセスしてください",
            background="サードパーティライブラリがプロジェクト全体に散在すると、依存関係の不透明化・ライブラリ置換の困難さ・アーキテクチャ境界の崩壊を招きます。特定のディレクトリ（基盤レイヤー等）に集約することで外部依存の境界が明確になります。",
            steps=(
                "許可ディレクトリ（allow-dirs）の設定を確認する",
                "許可ディレクトリ外でのサードパーティインポートを特定する",
                "サードパーティの利用を許可ディレクトリ配下のモジュールに移動するか、ラッパーモジュール経由でアクセスするよう修正する",
            ),
            config_example='[tool.paladin.rule.no-third-party-import]\nallow-dirs = ["src/myapp/foundation/"]\nallow-files = ["src/myapp/cli.py"]',
            detection_example="# 違反: 許可ディレクトリ外でサードパーティをインポート\n# src/myapp/services/user.py\nimport pydantic_settings  # 違反\n\n# 準拠: 許可ディレクトリ内でのインポート\n# src/myapp/foundation/model/base.py\nimport pydantic  # 準拠",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def prepare(self, source_files: SourceFiles) -> None:
        """実行前の事前準備：source_files からルートパッケージを自動導出する"""
        self._root_packages = self._resolver.resolve_root_packages(source_files)

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        if ThirdPartyChecker.is_allow_file(source_file.file_path, self._allow_files):
            return ()
        if ThirdPartyChecker.is_allowed_path(source_file.file_path, self._allow_dirs):
            return ()

        ctx = DetectionContext(meta=self._meta, source_file=source_file)
        violations: list[Violation] = []
        for stmt in source_file.imports:
            if stmt.is_relative:
                continue
            if stmt.is_import_from:
                violations.extend(self._check_from_import(ctx, stmt))
            else:
                violations.extend(self._check_plain_import(ctx, stmt))
        return tuple(violations)

    def _check_from_import(
        self,
        ctx: DetectionContext,
        stmt: ImportStatement,
    ) -> list[Violation]:
        top = stmt.top_level_module
        if top is None or not ThirdPartyChecker.is_third_party(
            top, self._stdlib_modules, self._root_packages
        ):
            return []
        return ThirdPartyImportDetector.detect_from_import(ctx, stmt)

    def _check_plain_import(
        self,
        ctx: DetectionContext,
        stmt: ImportStatement,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for imported in stmt.names:
            top = ModulePath(imported.name).top_level
            if not ThirdPartyChecker.is_third_party(top, self._stdlib_modules, self._root_packages):
                continue
            violations.append(
                ThirdPartyImportDetector.detect_plain_import(ctx, stmt, imported.name)
            )
        return violations
