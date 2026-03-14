"""RulesOrchestratorクラスのテスト"""

from paladin.lint import Rule, RuleRegistry
from paladin.rules.context import RulesContext
from paladin.rules.detail_formatter import RulesDetailFormatter
from paladin.rules.formatter import RulesFormatter
from paladin.rules.orchestrator import RulesOrchestrator
from tests.unit.test_check.fakes import FakeRule


class TestRulesOrchestrator:
    """RulesOrchestratorクラスのテスト"""

    def _make_orchestrator(self, rules: tuple[Rule, ...]) -> RulesOrchestrator:
        registry = RuleRegistry(rules=rules)
        formatter = RulesFormatter()
        detail_formatter = RulesDetailFormatter()
        return RulesOrchestrator(
            registry=registry, formatter=formatter, detail_formatter=detail_formatter
        )

    def test_orchestrate_正常系_rule_id未指定で既存の全ルール一覧を返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001", rule_name="fake-rule", summary="フェイク概要")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = RulesContext()

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert "PAL001" in result
        assert "fake-rule" in result
        assert "フェイク概要" in result

    def test_orchestrate_エッジケース_ルール未登録でrule_id未指定のとき空文字列を返すこと(self):
        # Arrange
        orchestrator = self._make_orchestrator(rules=())
        context = RulesContext()

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert result == ""

    def test_orchestrate_正常系_rule_id指定で対象ルールの詳細を返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001", rule_name="fake-rule", summary="フェイク概要")
        orchestrator = self._make_orchestrator(rules=(fake_rule,))
        context = RulesContext(rule_id="PAL001")

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
        context = RulesContext(rule_id="nonexistent")

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert "nonexistent" in result
        assert "Error" in result
