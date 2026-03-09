from pathlib import Path

from paladin.check.context import CheckContext


class TestCheckContext:
    """CheckContextクラスのテスト"""

    def test_init_正常系_属性が正しく保持されること(self):
        # Arrange
        targets = (Path("src/"),)

        # Act
        context = CheckContext(targets=targets)

        # Assert
        assert context.targets == targets
