"""OverrideResolver のテスト"""

from pathlib import Path

from paladin.check.override import OverrideResolver
from paladin.config import OverrideEntry


class TestOverrideResolver:
    """OverrideResolver.resolve のテスト"""

    def test_resolve_正常系_マッチするオーバーライドのrulesをbase_rulesにマージして返すこと(self):
        # Arrange
        override = OverrideEntry(
            files=("tests/**",),
            rules={"require-all-export": False},
        )
        resolver = OverrideResolver()
        file_path = Path("/project/tests/unit/test_foo.py")
        base_rules: dict[str, bool] = {"no-relative-import": True}

        # Act
        result = resolver.resolve((override,), file_path, base_rules)

        # Assert
        assert result == {"no-relative-import": True, "require-all-export": False}

    def test_resolve_正常系_後に定義されたオーバーライドが優先されること(self):
        # Arrange: 同一ファイルにマッチする2つのオーバーライド
        override1 = OverrideEntry(
            files=("tests/**",),
            rules={"require-all-export": False},
        )
        override2 = OverrideEntry(
            files=("tests/unit/**",),
            rules={"require-all-export": True},
        )
        resolver = OverrideResolver()
        file_path = Path("/project/tests/unit/test_foo.py")
        base_rules: dict[str, bool] = {}

        # Act
        result = resolver.resolve((override1, override2), file_path, base_rules)

        # Assert: 後に定義された override2 が優先される
        assert result == {"require-all-export": True}

    def test_resolve_正常系_オーバーライドで指定されていない設定はbase_rulesを引き継ぐこと(self):
        # Arrange
        override = OverrideEntry(
            files=("tests/**",),
            rules={"require-all-export": False},
        )
        resolver = OverrideResolver()
        file_path = Path("/project/tests/test_foo.py")
        base_rules: dict[str, bool] = {"no-relative-import": True, "no-local-import": True}

        # Act
        result = resolver.resolve((override,), file_path, base_rules)

        # Assert: base_rules の no-relative-import / no-local-import が引き継がれる
        assert result["no-relative-import"] is True
        assert result["no-local-import"] is True
        assert result["require-all-export"] is False

    def test_resolve_正常系_相対パスのglobパターンにマッチすること(self):
        # Arrange: 相対パターン "tests/**" が絶対パスにマッチすること
        override = OverrideEntry(
            files=("tests/**",),
            rules={"require-all-export": False},
        )
        resolver = OverrideResolver()
        file_path = Path("/any/project/tests/unit/test_foo.py")
        base_rules: dict[str, bool] = {}

        # Act
        result = resolver.resolve((override,), file_path, base_rules)

        # Assert
        assert result == {"require-all-export": False}

    def test_resolve_正常系_絶対パスにも正しくマッチすること(self):
        # Arrange: 絶対パターン
        override = OverrideEntry(
            files=("/project/tests/**",),
            rules={"require-all-export": False},
        )
        resolver = OverrideResolver()
        file_path = Path("/project/tests/unit/test_foo.py")
        base_rules: dict[str, bool] = {}

        # Act
        result = resolver.resolve((override,), file_path, base_rules)

        # Assert
        assert result == {"require-all-export": False}

    def test_resolve_エッジケース_マッチしない場合base_rulesをそのまま返すこと(self):
        # Arrange
        override = OverrideEntry(
            files=("tests/**",),
            rules={"require-all-export": False},
        )
        resolver = OverrideResolver()
        file_path = Path("/project/src/main.py")
        base_rules: dict[str, bool] = {"no-relative-import": True}

        # Act
        result = resolver.resolve((override,), file_path, base_rules)

        # Assert: マッチしないため base_rules そのまま
        assert result == {"no-relative-import": True}

    def test_resolve_エッジケース_overridesが空の場合base_rulesを返すこと(self):
        # Arrange
        resolver = OverrideResolver()
        file_path = Path("/project/src/main.py")
        base_rules: dict[str, bool] = {"no-relative-import": True}

        # Act
        result = resolver.resolve((), file_path, base_rules)

        # Assert
        assert result == {"no-relative-import": True}

    def test_resolve_エッジケース_filesに複数パターンがある場合いずれかにマッチすれば適用されること(
        self,
    ):
        # Arrange
        override = OverrideEntry(
            files=("scripts/**", "tools/**"),
            rules={"no-local-import": False},
        )
        resolver = OverrideResolver()
        file_path = Path("/project/tools/helper.py")
        base_rules: dict[str, bool] = {}

        # Act
        result = resolver.resolve((override,), file_path, base_rules)

        # Assert: tools/** にマッチ
        assert result == {"no-local-import": False}

    def test_resolve_エッジケース_前のオーバーライドの設定は引き継がれないこと(self):
        # Arrange: override1 と override2 がともにマッチするが後勝ちのため override2 のみ適用
        override1 = OverrideEntry(
            files=("tests/**",),
            rules={"require-all-export": False, "no-local-import": False},
        )
        override2 = OverrideEntry(
            files=("tests/unit/**",),
            rules={"require-all-export": True},
        )
        resolver = OverrideResolver()
        file_path = Path("/project/tests/unit/test_foo.py")
        base_rules: dict[str, bool] = {}

        # Act
        result = resolver.resolve((override1, override2), file_path, base_rules)

        # Assert: override2 の rules のみが base_rules にマージされる
        # override1 の no-local-import は引き継がれない
        assert result == {"require-all-export": True}
        assert "no-local-import" not in result
