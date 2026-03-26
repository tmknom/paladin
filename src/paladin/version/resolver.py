"""importlib.metadata を通じてインストール済みパッケージのバージョンを解決する。

実行環境にパッケージがインストールされていない場合は例外が送出される。
"""

import importlib.metadata

from paladin.foundation.log import log


class VersionResolver:
    """パッケージのバージョン文字列を解決する"""

    def __init__(self, package_name: str) -> None:
        """VersionResolverを初期化する"""
        self.package_name = package_name

    @log
    def resolve(self) -> str:
        """パッケージのバージョン文字列を返す。

        Raises:
            importlib.metadata.PackageNotFoundError: パッケージが実行環境にインストールされていない場合。
        """
        return importlib.metadata.version(self.package_name)
