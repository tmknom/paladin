from paladin.lint.protocol import Rule
from paladin.lint.types import RuleMeta, Violation
from paladin.source.types import ParsedFile


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
                    intent="スタブ意図",
                    guidance="スタブ見方",
                    suggestion="スタブ修正方向",
                )

            def check(self, parsed_file: ParsedFile) -> tuple[Violation, ...]:
                return ()

        stub = StubRule()

        # Act & Assert
        assert isinstance(stub, Rule)
