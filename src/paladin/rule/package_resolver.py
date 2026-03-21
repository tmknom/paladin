"""パッケージパス解決ユーティリティ

ファイルパスから Python パッケージ名を導出するロジックを提供する。
NoDirectInternalImportRule と RequireQualifiedThirdPartyRule で共有する。
"""

from pathlib import Path

from paladin.rule.types import SourceFiles

# src レイアウト固有のディレクトリ名（パッケージセグメントから除外する）
NON_PACKAGE_DIRS: frozenset[str] = frozenset({"src", "tests"})


class PackageResolver:
    """ファイルパスから Python パッケージ名を解決するユーティリティ"""

    def resolve_package_key(self, file_path: Path) -> str | None:
        """ファイルパスからパッケージキー（先頭2セグメント）を取得する

        例: src/paladin/check/__init__.py -> "paladin.check"
             src/paladin/check/foo.py    -> "paladin.check"
             /abs/path/src/paladin/check/foo.py -> "paladin.check"
             tests/unit/test_check/foo.py -> "tests.unit"
        """
        parts = self._resolve_package_parts(file_path)
        return ".".join(parts[:2]) if parts else None

    def resolve_exact_package_path(self, file_path: Path) -> str | None:
        """__init__.py のファイルパスから正確なパッケージパスを取得する

        例: src/paladin/foundation/model/__init__.py -> "paladin.foundation.model"
             src/paladin/check/__init__.py           -> "paladin.check"
             tests/unit/fakes/__init__.py            -> "tests.unit.fakes"
        """
        parts = self._resolve_package_parts(file_path)
        return ".".join(parts) if parts else None

    def _resolve_package_parts(self, file_path: Path) -> list[str] | None:
        """ファイルパスからパッケージ構成要素のリストを返す（2セグメント未満なら None）"""
        dir_parts = file_path.parts[:-1]
        anchor_index, anchor_name = self._find_anchor(dir_parts)
        if anchor_index >= 0:
            package_parts = list(dir_parts[anchor_index + 1 :])
            if anchor_name == "tests":
                package_parts = ["tests", *package_parts]
        else:
            package_parts = [
                p for p in dir_parts if not p.startswith(".") and p not in NON_PACKAGE_DIRS
            ]
        if len(package_parts) < 2:
            return None
        return package_parts

    @staticmethod
    def is_same_package_exact(pkg_a: str | None, pkg_b: str | None) -> bool:
        """2つのパッケージキーが完全一致するか判定する"""
        if pkg_a is None or pkg_b is None:
            return False
        return pkg_a == pkg_b

    @staticmethod
    def is_own_package(import_package: str, own_packages: frozenset[str]) -> bool:
        """import_package が own_packages のいずれかに属するか判定する（双方向プレフィックス一致）"""
        if import_package in own_packages:
            return True
        prefix = import_package + "."
        return any(pkg.startswith(prefix) for pkg in own_packages)

    def resolve_root_packages(self, source_files: SourceFiles) -> tuple[str, ...]:
        """全ファイルからルートパッケージ名を導出する

        各ファイルの NON_PACKAGE_DIRS アンカー後の最初のセグメントを収集し、
        "tests" を常に含める。

        src/ 由来のルートパッケージが見つからない場合（tests/ のみを解析対象にした場合など）、
        tests アンカーの親ディレクトリ（プロジェクトルート候補）の src/ を走査してフォールバックする。

        例: src/paladin/check/foo.py -> "paladin"
             src/mylib/core.py       -> "mylib"
        """
        root_packages: set[str] = {"tests"}
        project_root_candidates: set[Path] = set()

        for source_file in source_files:
            self._collect_from_file(source_file.file_path, root_packages, project_root_candidates)

        # src/ 由来のパッケージが見つからない場合、FS フォールバックで補完する
        if len(root_packages) == 1:  # "tests" のみ
            self._fallback_from_filesystem(project_root_candidates, root_packages)

        return tuple(sorted(root_packages))

    def _collect_from_file(
        self,
        file_path: Path,
        root_packages: set[str],
        project_root_candidates: set[Path],
    ) -> None:
        """1ファイルからルートパッケージとプロジェクトルート候補を収集する"""
        dir_parts = file_path.parts[:-1]
        anchor_index, anchor_name = self._find_anchor(dir_parts)

        if anchor_index < 0:
            return

        if anchor_name == "src":
            after_src = dir_parts[anchor_index + 1 :]
            if after_src:
                root_packages.add(after_src[0])
        elif anchor_name == "tests":
            tests_anchor_path = Path(*dir_parts[: anchor_index + 1])
            project_root_candidates.add(tests_anchor_path.parent)

    def _fallback_from_filesystem(
        self, project_root_candidates: set[Path], root_packages: set[str]
    ) -> None:
        """プロジェクトルート候補の src/ ディレクトリを走査してルートパッケージを補完する"""
        for candidate in project_root_candidates:
            src_dir = candidate / "src"
            if not src_dir.is_dir():
                continue
            self._collect_packages_from_src(src_dir, root_packages)

    def _collect_packages_from_src(self, src_dir: Path, root_packages: set[str]) -> None:
        """src/ ディレクトリ直下のパッケージを収集する"""
        for child in src_dir.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                root_packages.add(child.name)

    def _find_anchor(self, dir_parts: tuple[str, ...]) -> tuple[int, str]:
        """NON_PACKAGE_DIRS の最後の出現位置をアンカーとして返す

        Returns:
            (anchor_index, anchor_name)。見つからない場合は (-1, "")
        """
        anchor_index = -1
        anchor_name = ""
        for i, p in enumerate(dir_parts):
            if p in NON_PACKAGE_DIRS:
                anchor_index = i
                anchor_name = p
        return anchor_index, anchor_name
