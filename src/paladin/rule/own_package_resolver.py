"""自パッケージ解決ドメインサービス"""

from pathlib import Path

from paladin.rule.package_resolver import PackageResolver


class OwnPackageResolver:
    """ファイルが属する自パッケージのセットを解決するドメインサービス"""

    def __init__(self) -> None:
        """ドメインサービスを初期化する"""
        self._resolver = PackageResolver()

    def resolve(self, file_path: Path, root_packages: tuple[str, ...]) -> frozenset[str]:
        """ファイルが属する「自パッケージ」のセットを返す

        通常は resolve_package_key の結果のみ。
        テストファイル（tests/ 配下の test_xxx/test_yyy.py）の場合は、
        対応するプロダクションパッケージも同一視する。

        例: tests/unit/test_view/test_provider.py
              -> {"tests.unit", "paladin.view"}  # resolve_package_key + "test_" 除去で対応パッケージを算出
        """
        package_key = self._resolver.resolve_package_key(file_path)
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

        after_tests = dir_parts[tests_index + 1 :]
        # "test_" プレフィックスを持つ最初のディレクトリからプロダクションパッケージを算出する。
        # パッケージキーは常に先頭2セグメントで定義されるため、最初の test_ ディレクトリのみ使う。
        # これにより tests/unit/test_check/test_ignore/ のようなネスト深度に関係なく
        # 常に "paladin.check" という2セグメントのキーが生成される。
        test_dirs = [p[len("test_") :] for p in after_tests if p.startswith("test_")]
        if not test_dirs:
            return frozenset(own)

        production_subpkg = test_dirs[0]
        for root_pkg in root_packages:
            own.add(f"{root_pkg}.{production_subpkg}")

        return frozenset(own)
