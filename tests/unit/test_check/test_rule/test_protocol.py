from paladin.check.rule.protocol import Rule
from paladin.check.rule.types import RuleMeta, Violation
from paladin.check.types import ParsedFile


class TestRuleProtocol:
    """Rule Protocolのテスト"""

    def test_rule_protocol_正常系_構造的部分型として認識されること(self):
        # Arrange: Rule Protocol に適合するスタブクラスをローカルに定義
        class StubRule:
            @property
            def meta(self) -> RuleMeta:
                return RuleMeta(
                    rule_id="stub-rule",
                    rule_name="Stub Rule",
                    summary="スタブルール",
                )

            def check(self, parsed_file: ParsedFile) -> tuple[Violation, ...]:
                return ()

        stub = StubRule()

        # Act & Assert
        assert isinstance(stub, Rule)
