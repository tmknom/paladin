"""値オブジェクト生成ファクトリ"""

from paladin.rule import RuleMeta


class RuleMetaFactory:
    """テスト用 RuleMeta 生成ファクトリ"""

    @staticmethod
    def make(  # paladin: ignore[max-function-parameter]
        rule_id: str = "PAL001",
        rule_name: str = "rule-name",
        summary: str = "概要テキスト",
        intent: str = "意図",
        guidance: str = "見方",
        suggestion: str = "修正方向",
    ) -> RuleMeta:
        return RuleMeta(
            rule_id=rule_id,
            rule_name=rule_name,
            summary=summary,
            intent=intent,
            guidance=guidance,
            suggestion=suggestion,
        )
