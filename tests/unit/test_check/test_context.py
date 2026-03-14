from pathlib import Path

from paladin.check.context import CheckContext
from paladin.check.types import OutputFormat


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

    def test_CheckContext_正常系_has_cli_targetsをTrueに設定できること(self):
        # Arrange & Act
        context = CheckContext(targets=(Path("src/"),), has_cli_targets=True)

        # Assert
        assert context.has_cli_targets is True

    def test_CheckContext_正常系_デフォルトでhas_cli_targetsがFalseであること(self):
        # Arrange & Act
        context = CheckContext(targets=(Path("src/"),))

        # Assert
        assert context.has_cli_targets is False
