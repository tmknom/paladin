from pathlib import Path

from paladin.check.context import CheckContext
from paladin.foundation.output import OutputFormat
from paladin.rule import OverrideEntry


class TestCheckContext:
    """CheckContextクラスのテスト"""

    def test_init_正常系_属性が正しく保持されること(self):
        # Arrange
        targets = (Path("src/"),)

        # Act
        context = CheckContext(targets=targets)

        # Assert
        assert context.targets == targets

    def test_init_正常系_format属性がデフォルトでTEXTであること(self):
        # Arrange & Act
        context = CheckContext(targets=(Path("src/"),))

        # Assert
        assert context.format == OutputFormat.TEXT

    def test_init_正常系_format属性にJSONを指定できること(self):
        # Arrange & Act
        context = CheckContext(targets=(Path("src/"),), format=OutputFormat.JSON)

        # Assert
        assert context.format == OutputFormat.JSON

    def test_init_正常系_ignore_rulesを保持できること(self):
        # Arrange & Act
        context = CheckContext(targets=(Path("src/"),), ignore_rules=frozenset({"rule-a"}))

        # Assert
        assert context.ignore_rules == frozenset({"rule-a"})

    def test_init_エッジケース_ignore_rulesのデフォルトが空frozensetであること(self):
        # Arrange & Act
        context = CheckContext(targets=(Path("src/"),))

        # Assert
        assert context.ignore_rules == frozenset()

    def test_CheckContext_正常系_overridesフィールドを保持できること(self):
        # Arrange
        entry = OverrideEntry(files=("tests/**",), rules={"require-all-export": False})

        # Act
        context = CheckContext(targets=(Path("src/"),), overrides=(entry,))

        # Assert
        assert context.overrides == (entry,)

    def test_CheckContext_正常系_デフォルトでoverridesが空タプルであること(self):
        # Arrange & Act
        context = CheckContext(targets=(Path("src/"),))

        # Assert
        assert context.overrides == ()
