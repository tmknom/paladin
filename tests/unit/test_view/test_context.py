"""ViewContextクラスのテスト"""

from paladin.foundation.output import OutputFormat
from paladin.view.context import ViewContext


class TestViewContext:
    """ViewContextクラスのテスト"""

    def test_format_未指定時のデフォルトがTEXTであること(self):
        # Act
        result = ViewContext(rule_id="test")

        # Assert
        assert result.format == OutputFormat.TEXT

    def test_format_JSON指定で保持されること(self):
        # Act
        result = ViewContext(rule_id="test", format=OutputFormat.JSON)

        # Assert
        assert result.format == OutputFormat.JSON
