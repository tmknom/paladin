"""ViewContextクラスのテスト"""

from paladin.check import OutputFormat
from paladin.view.context import ViewContext


class TestViewContext:
    """ViewContextクラスのテスト"""

    def test_ViewContext_正常系_rule_id指定でインスタンス生成できること(self):
        # Act
        result = ViewContext(rule_id="require-all-export")

        # Assert
        assert result.rule_id == "require-all-export"

    def test_ViewContext_正常系_format未指定でデフォルトがTEXTであること(self):
        # Act
        result = ViewContext(rule_id="test")

        # Assert
        assert result.format == OutputFormat.TEXT

    def test_ViewContext_正常系_format指定でJSON形式を保持すること(self):
        # Act
        result = ViewContext(rule_id="test", format=OutputFormat.JSON)

        # Assert
        assert result.format == OutputFormat.JSON
