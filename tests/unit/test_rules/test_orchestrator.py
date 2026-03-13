"""RulesOrchestratorクラスのテスト"""

from paladin.check.rule.registry import RuleRegistry
from paladin.rules.formatter import RulesFormatter
from paladin.rules.orchestrator import RulesOrchestrator
from tests.unit.test_check.fakes import FakeRule


class TestRulesOrchestrator:
    """RulesOrchestratorクラスのテスト"""

    def test_orchestrate_正常系_登録済みルールをフォーマットした文字列を返すこと(self):
        # Arrange
        fake_rule = FakeRule(rule_id="PAL001", rule_name="fake-rule", summary="フェイク概要")
        registry = RuleRegistry(rules=(fake_rule,))
        formatter = RulesFormatter()
        orchestrator = RulesOrchestrator(registry=registry, formatter=formatter)

        # Act
        result = orchestrator.orchestrate()

        # Assert
        assert "PAL001" in result
        assert "fake-rule" in result
        assert "フェイク概要" in result

    def test_orchestrate_エッジケース_ルール未登録で空文字列を返すこと(self):
        # Arrange
        registry = RuleRegistry(rules=())
        formatter = RulesFormatter()
        orchestrator = RulesOrchestrator(registry=registry, formatter=formatter)

        # Act
        result = orchestrator.orchestrate()

        # Assert
        assert result == ""
