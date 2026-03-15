"""内部モジュールへの直接インポート禁止ルール

仕様は docs/rules/no-direct-internal-import.md を参照。
"""

import ast
from pathlib import Path

from paladin.lint.types import RuleMeta, SourceFile, SourceFiles, Violation

# src レイアウト固有のディレクトリ名（パッケージセグメントから除外する）
_NON_PACKAGE_DIRS: frozenset[str] = frozenset({"src", "tests"})


class NoDirectInternalImportRule:
    """他パッケージの内部モジュールへの直接インポートを検出するルール"""

    def __init__(self, root_packages: tuple[str, ...]) -> None:
        """ルールを初期化する

        Args:
            root_packages: 自プロジェクトのルートパッケージ名群
        """
        self._root_packages = root_packages
        self._meta = RuleMeta(
            rule_id="no-direct-internal-import",
            rule_name="No Direct Internal Import",
            summary="他パッケージの内部モジュールへの直接インポートを禁止する",
            intent="パッケージの公開 API を経由した依存を促し、内部実装への依存を排除する",
            guidance="from package.submodule.internal import Foo のような3階層以上のインポートを確認する",
            suggestion="パッケージの __init__.py を経由するインポートに書き換える",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_files: SourceFiles) -> tuple[Violation, ...]:
        """複数ファイルに対する違反判定を行う"""
        if not self._root_packages:
            return ()

        package_exports = self._build_package_exports(source_files)
        src_root = self._infer_src_root(source_files)
        violations: list[Violation] = []

        for source_file in source_files:
            violations.extend(self._check_file(source_file, package_exports, src_root))

        return tuple(violations)

    def _infer_src_root(self, source_files: SourceFiles) -> Path | None:
        """source_files のパスから src/ ディレクトリを推定する

        _NON_PACKAGE_DIRS に含まれるアンカー（src or tests）の親ディレクトリを
        プロジェクトルートとして算出し、<project_root>/src を返す。
        """
        for source_file in source_files:
            parts = source_file.file_path.parts
            for i, part in enumerate(parts):
                if part in _NON_PACKAGE_DIRS:
                    project_root = Path(*parts[:i]) if i > 0 else Path()
                    src_root = project_root / "src"
                    if src_root.is_dir():
                        return src_root
        return None

    def _is_subpackage_on_filesystem(self, module_path: str, src_root: Path | None) -> bool:
        """module_path に対応する src/ 配下のディレクトリに __init__.py が存在するかを確認する"""
        if src_root is None:
            return False
        segments = module_path.split(".")
        package_dir = src_root.joinpath(*segments)
        return (package_dir / "__init__.py").is_file()

    def _build_package_exports(self, source_files: SourceFiles) -> dict[str, set[str]]:
        """__init__.py を解析して、パッケージパス -> 公開シンボルセットのマッピングを構築する

        キーは先頭2セグメントではなく正確なパッケージパス（全セグメント）を使用する。
        例: src/paladin/foundation/model/__init__.py -> "paladin.foundation.model"
        """
        package_exports: dict[str, set[str]] = {}

        for source_file in source_files:
            if source_file.file_path.name != "__init__.py":
                continue

            exact_key = self._resolve_exact_package_path(source_file.file_path)
            if exact_key is None:
                continue

            exports = self._collect_exports(source_file)
            package_exports[exact_key] = exports

        return package_exports

    def _resolve_exact_package_path(self, file_path: Path) -> str | None:
        """__init__.py のファイルパスから正確なパッケージパスを取得する

        例: src/paladin/foundation/model/__init__.py -> "paladin.foundation.model"
             src/paladin/check/__init__.py           -> "paladin.check"
             tests/unit/fakes/__init__.py            -> "tests.unit.fakes"
        """
        dir_parts = file_path.parts[:-1]  # ファイル名を除く

        anchor_index = -1
        anchor_name = ""
        for i, p in enumerate(dir_parts):
            if p in _NON_PACKAGE_DIRS:
                anchor_index = i
                anchor_name = p

        if anchor_index >= 0:
            package_parts = list(dir_parts[anchor_index + 1 :])
            # tests は Python インポートパスの一部なので先頭に復元する
            if anchor_name == "tests":
                package_parts = ["tests", *package_parts]
        else:
            package_parts = [
                p for p in dir_parts if not p.startswith(".") and p not in _NON_PACKAGE_DIRS
            ]

        if len(package_parts) < 2:
            return None

        return ".".join(package_parts)

    def _resolve_package_key(self, file_path: Path) -> str | None:
        """ファイルパスからパッケージキー（先頭2セグメント）を取得する

        例: src/paladin/check/__init__.py -> "paladin.check"
             src/paladin/check/foo.py    -> "paladin.check"
             /abs/path/src/paladin/check/foo.py -> "paladin.check"
             tests/unit/test_check/foo.py -> "tests.unit"
        """
        dir_parts = file_path.parts[:-1]  # ファイル名を除く

        # _NON_PACKAGE_DIRS の最後の出現位置をアンカーとして使用する
        # （絶対パスでも相対パスでも正しく動作させるため）
        anchor_index = -1
        anchor_name = ""
        for i, p in enumerate(dir_parts):
            if p in _NON_PACKAGE_DIRS:
                anchor_index = i
                anchor_name = p

        if anchor_index >= 0:
            package_parts = list(dir_parts[anchor_index + 1 :])
            # tests は Python インポートパスの一部なので先頭に復元する
            if anchor_name == "tests":
                package_parts = ["tests", *package_parts]
        else:
            # フォールバック: アンカーが見つからない場合は旧ロジック
            package_parts = [
                p for p in dir_parts if not p.startswith(".") and p not in _NON_PACKAGE_DIRS
            ]

        if len(package_parts) < 2:
            return None

        return ".".join(package_parts[:2])

    def _resolve_own_packages(self, file_path: Path) -> frozenset[str]:
        """ファイルが属する「自パッケージ」のセットを返す

        通常は _resolve_package_key の結果のみ。
        テストファイル（tests/ 配下の test_xxx/test_yyy.py）の場合は、
        対応するプロダクションパッケージも同一視する。

        例: tests/unit/test_view/test_provider.py
              -> {"tests.unit", "paladin.view"}  # _resolve_package_key + "test_" 除去で対応パッケージを算出
        """
        package_key = self._resolve_package_key(file_path)
        own: set[str] = set()
        if package_key is not None:
            own.add(package_key)

        # tests/ 配下かどうかを判定する
        if "tests" not in file_path.parts:
            return frozenset(own)

        # tests/ 以降のパス部分から対応プロダクションパッケージを算出する
        # tests/unit/test_view/test_provider.py
        #   -> tests アンカー以降: ["unit", "test_view"]
        #   -> "test_" を除いた最後のディレクトリ名: "view"
        #   -> root_packages の先頭 + "view" = "paladin.view"
        dir_parts = file_path.parts[:-1]
        tests_index = -1
        for i, p in enumerate(dir_parts):
            if p == "tests":
                tests_index = i

        if tests_index < 0:
            return frozenset(own)

        after_tests = list(dir_parts[tests_index + 1 :])
        # "test_" プレフィックスを持つディレクトリのみを順番に抽出して連結する
        # tests/unit/test_foundation/test_error/ → ["foundation", "error"]
        #   → "foundation.error" → "paladin.foundation.error"
        test_dirs = [p[len("test_") :] for p in after_tests if p.startswith("test_")]
        if not test_dirs:
            return frozenset(own)

        production_subpkg = ".".join(test_dirs)
        for root_pkg in self._root_packages:
            own.add(f"{root_pkg}.{production_subpkg}")

        return frozenset(own)

    def _collect_exports(self, source_file: SourceFile) -> set[str]:
        """__init__.py の AST から公開シンボルセットを収集する

        __all__ の定義と from .xxx import yyy の再エクスポートを収集する。
        """
        exports: set[str] = set()

        for node in ast.walk(source_file.tree):
            # __all__ = ["Foo", "Bar"] の形式
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "__all__"
                and isinstance(node.value, (ast.List, ast.Tuple))
            ):
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        exports.add(elt.value)

            # from .xxx import Foo の形式（相対インポートのみ対象）
            if (
                isinstance(node, ast.ImportFrom)
                and node.level >= 1  # 相対インポート
                and node.names
            ):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    exports.add(name)

        return exports

    def _check_file(
        self,
        source_file: SourceFile,
        package_exports: dict[str, set[str]],
        src_root: Path | None = None,
    ) -> list[Violation]:
        """1ファイルの ImportFrom ノードを走査して違反を収集する"""
        violations: list[Violation] = []
        own_packages = self._resolve_own_packages(source_file.file_path)

        for node in ast.walk(source_file.tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level != 0:  # 相対インポートは対象外
                continue
            if node.module is None:
                continue

            segments = node.module.split(".")
            if len(segments) < 3:  # 3階層未満は対象外
                continue

            top_pkg = segments[0]
            if top_pkg not in self._root_packages:
                continue

            import_package = ".".join(segments[:2])

            # 同一パッケージ（またはテストの対応プロダクションパッケージ）は対象外
            # own_packages が import_package より深い階層を持つ場合もプレフィックス一致で判定する
            # 例: own = {"paladin.foundation.error"}, import = "paladin.foundation" → 除外
            if self._is_own_package(import_package, own_packages):
                continue

            # インポートモジュール自体がサブパッケージ（__init__.py を持つ）なら対象外
            # 例: from paladin.foundation.model import X → paladin.foundation.model はサブパッケージ
            if node.module in package_exports:
                continue
            # source_files に含まれない __init__.py はファイルシステムで確認する
            if self._is_subpackage_on_filesystem(node.module, src_root):
                continue

            for alias in node.names:
                name = alias.name
                if self._should_report(name, import_package, package_exports):
                    violations.append(self._make_violation(source_file, node, name, import_package))

        return violations

    def _is_own_package(self, import_package: str, own_packages: frozenset[str]) -> bool:
        """import_package が自パッケージセットに属するかを判定する

        完全一致に加え、own_packages の要素が import_package のサブパッケージである場合もマッチする。
        例: import_package = "paladin.foundation", own = {"paladin.foundation.error"} -> True
        """
        if import_package in own_packages:
            return True
        prefix = import_package + "."
        return any(pkg.startswith(prefix) for pkg in own_packages)

    def _should_report(
        self,
        name: str,
        import_package: str,
        package_exports: dict[str, set[str]],
    ) -> bool:
        """違反として報告すべきかを判定する"""
        if import_package not in package_exports:
            # __init__.py が解析対象にない場合はヒューリスティック検出
            return True

        exports = package_exports[import_package]
        if not exports:
            # __init__.py が存在するがエクスポートが空の場合もヒューリスティック検出
            return True

        # __init__.py で公開されているシンボルのみを違反として報告
        return name in exports

    def _make_violation(
        self,
        source_file: SourceFile,
        node: ast.ImportFrom,
        name: str,
        package: str,
    ) -> Violation:
        """違反オブジェクトを生成する"""
        module_path = node.module or ""
        return Violation(
            file=source_file.file_path,
            line=node.lineno,
            column=node.col_offset,
            rule_id=self._meta.rule_id,
            rule_name=self._meta.rule_name,
            message=f"`from {module_path} import {name}` は内部モジュールへの直接参照である",
            reason=f"`{package}` の内部実装に直接依存しており、パッケージの公開 API を経由していない",
            suggestion=f"`from {package} import {name}` のように、パッケージの `__init__.py` を経由するインポートに書き換える",
        )
