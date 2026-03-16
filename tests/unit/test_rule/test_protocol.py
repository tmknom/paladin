from paladin.rule.protocol import MultiFileRule, Rule
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


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

            def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
                return ()

        stub = StubRule()

        # Act & Assert
        assert isinstance(stub, Rule)


class TestMultiFileRuleProtocol:
    """MultiFileRule Protocolのテスト"""

    def test_multi_file_rule_protocol_正常系_構造的部分型として認識されること(self):
        # Arrange: MultiFileRule Protocol に適合するスタブクラスをローカルに定義
        class StubMultiFileRule:
            @property
            def meta(self) -> RuleMeta:
                return RuleMeta(
                    rule_id="stub-multi-rule",
                    rule_name="Stub Multi Rule",
                    summary="スタブ複数ファイルルール",
                    intent="スタブ意図",
                    guidance="スタブ見方",
                    suggestion="スタブ修正方向",
                )

            def check(self, source_files: SourceFiles) -> tuple[Violation, ...]:
                return ()

        stub = StubMultiFileRule()

        # Act & Assert
        assert isinstance(stub, MultiFileRule)
