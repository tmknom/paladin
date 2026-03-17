"""パッケージパス解決ユーティリティ

ファイルパスから Python パッケージ名を導出するロジックを提供する。
NoDirectInternalImportRule と RequireQualifiedThirdPartyRule で共有する。
"""

from pathlib import Path

from paladin.rule.types import SourceFiles

# src レイアウト固有のディレクトリ名（パッケージセグメントから除外する）
_NON_PACKAGE_DIRS: frozenset[str] = frozenset({"src", "tests"})


class PackageResolver:
    """ファイルパスから Python パッケージ名を解決するユーティリティ"""

    def resolve_package_key(self, file_path: Path) -> str | None:
        """ファイルパスからパッケージキー（先頭2セグメント）を取得する

        例: src/paladin/check/__init__.py -> "paladin.check"
             src/paladin/check/foo.py    -> "paladin.check"
             /abs/path/src/paladin/check/foo.py -> "paladin.check"
             tests/unit/test_check/foo.py -> "tests.unit"
        """
        dir_parts = file_path.parts[:-1]  # ファイル名を除く

        anchor_index, anchor_name = self._find_anchor(dir_parts)

        if anchor_index >= 0:
            package_parts = list(dir_parts[anchor_index + 1 :])
            if anchor_name == "tests":
                package_parts = ["tests", *package_parts]
        else:
            package_parts = [
                p for p in dir_parts if not p.startswith(".") and p not in _NON_PACKAGE_DIRS
            ]

        if len(package_parts) < 2:
            return None

        return ".".join(package_parts[:2])

    def resolve_exact_package_path(self, file_path: Path) -> str | None:
        """__init__.py のファイルパスから正確なパッケージパスを取得する

        例: src/paladin/foundation/model/__init__.py -> "paladin.foundation.model"
             src/paladin/check/__init__.py           -> "paladin.check"
             tests/unit/fakes/__init__.py            -> "tests.unit.fakes"
        """
        dir_parts = file_path.parts[:-1]  # ファイル名を除く

        anchor_index, anchor_name = self._find_anchor(dir_parts)

        if anchor_index >= 0:
            package_parts = list(dir_parts[anchor_index + 1 :])
            if anchor_name == "tests":
                package_parts = ["tests", *package_parts]
        else:
            package_parts = [
                p for p in dir_parts if not p.startswith(".") and p not in _NON_PACKAGE_DIRS
            ]

        if len(package_parts) < 2:
            return None

        return ".".join(package_parts)

    def resolve_root_packages(self, source_files: SourceFiles) -> tuple[str, ...]:
        """全ファイルからルートパッケージ名を導出する

        各ファイルの _NON_PACKAGE_DIRS アンカー後の最初のセグメントを収集し、
        "tests" を常に含める。

        例: src/paladin/check/foo.py -> "paladin"
             src/mylib/core.py       -> "mylib"
        """
        root_packages: set[str] = {"tests"}

        for source_file in source_files:
            dir_parts = source_file.file_path.parts[:-1]
            anchor_index, anchor_name = self._find_anchor(dir_parts)

            if anchor_index >= 0 and anchor_name == "src":
                after_src = dir_parts[anchor_index + 1 :]
                if after_src:
                    root_packages.add(after_src[0])

        return tuple(sorted(root_packages))

    def _find_anchor(self, dir_parts: tuple[str, ...]) -> tuple[int, str]:
        """_NON_PACKAGE_DIRS の最後の出現位置をアンカーとして返す

        Returns:
            (anchor_index, anchor_name)。見つからない場合は (-1, "")
        """
        anchor_index = -1
        anchor_name = ""
        for i, p in enumerate(dir_parts):
            if p in _NON_PACKAGE_DIRS:
                anchor_index = i
                anchor_name = p
        return anchor_index, anchor_name
