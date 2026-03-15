"""ViewContextクラスのテスト"""

from paladin.view.context import ViewContext


class TestViewContext:
    """ViewContextクラスのテスト"""

    def test_ViewContext_正常系_rule_id指定でインスタンス生成できること(self):
        # Act
        result = ViewContext(rule_id="require-all-export")

        # Assert
        assert result.rule_id == "require-all-export"
