from pathlib import Path

from paladin.rule.own_package_resolver import OwnPackageResolver

ROOT_PACKAGES = ("paladin",)
MULTI_ROOT_PACKAGES = ("myapp", "paladin")


class TestOwnPackageResolverResolve:
    """OwnPackageResolver.resolve のテスト"""

    def test_resolve_正常系_プロダクションファイルはpackage_keyのみを返すこと(self):
        # Arrange
        resolver = OwnPackageResolver()
        file_path = Path("src/paladin/check/formatter.py")

        # Act
        result = resolver.resolve(file_path, ROOT_PACKAGES)

        # Assert
        assert result == frozenset({"paladin.check"})

    def test_resolve_正常系_テストファイルはpackage_keyと対応プロダクションパッケージを返すこと(
        self,
    ):
        # Arrange
        resolver = OwnPackageResolver()
        file_path = Path("tests/unit/test_view/test_provider.py")

        # Act
        result = resolver.resolve(file_path, ROOT_PACKAGES)

        # Assert
        assert result == frozenset({"tests.unit", "paladin.view"})

    def test_resolve_正常系_ネストされたテストディレクトリは最初のtest_ディレクトリからパッケージを返すこと(
        self,
    ):
        # Arrange
        resolver = OwnPackageResolver()
        file_path = Path("tests/unit/test_foundation/test_error/test_handler.py")

        # Act
        result = resolver.resolve(file_path, ROOT_PACKAGES)

        # Assert: パッケージキーは先頭2セグメント固定のため、最初の test_ ディレクトリのみ使われる
        assert result == frozenset({"tests.unit", "paladin.foundation"})

    def test_resolve_正常系_複数root_packagesの場合は複数のプロダクションエントリを返すこと(self):
        # Arrange
        resolver = OwnPackageResolver()
        file_path = Path("tests/unit/test_check/test_formatter.py")

        # Act
        result = resolver.resolve(file_path, MULTI_ROOT_PACKAGES)

        # Assert
        assert result == frozenset({"tests.unit", "myapp.check", "paladin.check"})

    def test_resolve_正常系_tests配下だがtest_プレフィックスなしはpackage_keyのみを返すこと(self):
        # Arrange
        resolver = OwnPackageResolver()
        file_path = Path("tests/unit/fakes/fake_rule.py")

        # Act
        result = resolver.resolve(file_path, ROOT_PACKAGES)

        # Assert
        assert result == frozenset({"tests.unit"})

    def test_resolve_正常系_ファイル名がtestsでディレクトリでない場合はテストマッピングなし(self):
        # Arrange
        resolver = OwnPackageResolver()
        # "tests" がパスのパーツに含まれない（ファイル名ではなく）
        file_path = Path("src/paladin/check/tests.py")

        # Act
        result = resolver.resolve(file_path, ROOT_PACKAGES)

        # Assert
        assert result == frozenset({"paladin.check"})

    def test_resolve_正常系_ファイル名がtestsで拡張子なしの場合はテストマッピングなし(self):
        # Arrange
        resolver = OwnPackageResolver()
        # "tests" が file_path.parts に含まれる（拡張子なしファイル名）が、
        # dir_parts（ファイル名除く）には含まれず tests_index < 0 になる
        file_path = Path("src/paladin/check/tests")

        # Act
        result = resolver.resolve(file_path, ROOT_PACKAGES)

        # Assert
        assert result == frozenset({"paladin.check"})

    def test_resolve_正常系_package_keyがNoneの場合は空frozensetを返すこと(self):
        # Arrange
        resolver = OwnPackageResolver()
        # 1セグメントしかないパスは package_key が None
        file_path = Path("single_file.py")

        # Act
        result = resolver.resolve(file_path, ROOT_PACKAGES)

        # Assert
        assert result == frozenset()
