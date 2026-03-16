"""ViewOrchestratorクラスのテスト"""

from paladin.rule import Rule, RuleSet
from paladin.view.context import ViewContext
from paladin.view.formatter import ViewFormatter
from paladin.view.orchestrator import ViewOrchestrator
from tests.unit.fakes import FakeRule


class TestViewOrchestrator:
    """ViewOrchestratorクラスのテスト"""

    def _make_orchestrator(self, rules: tuple[Rule, ...]) -> ViewOrchestrator:
        rule_set = RuleSet(rules=rules)
        formatter = ViewFormatter()
        return ViewOrchestrator(rule_set=rule_set, formatter=formatter)

    def test_orchestrate_正常系_rule_id指定で対象ルールの詳細を返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001", rule_name="fake-rule", summary="フェイク概要")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = ViewContext(rule_id="PAL001")

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert "PAL001" in result
        assert "fake-rule" in result
        assert "フェイク概要" in result
        assert "Rule ID:" in result
        assert "Name:" in result
        assert "Summary:" in result
        assert "Intent:" in result
        assert "Guidance:" in result
        assert "Suggestion:" in result

    def test_orchestrate_エッジケース_存在しないrule_idでエラーメッセージを返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = ViewContext(rule_id="nonexistent")

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert "nonexistent" in result
        assert "Error" in result
