"""値オブジェクト生成ファクトリ"""

from paladin.rule import RuleMeta


class RuleMetaFactory:
    """テスト用 RuleMeta 生成ファクトリ（拡張版）"""

    @staticmethod
    def make(
        rule_id: str = "my-rule",
        rule_name: str = "My Rule",
        summary: str = "概要",
        intent: str = "意図",
        guidance: str = "見方",
        suggestion: str = "修正方向",
        background: str | None = None,
        steps: tuple[str, ...] | None = None,
        config_example: str | None = None,
        detection_example: str | None = None,
    ) -> RuleMeta:
        return RuleMeta(
            rule_id=rule_id,
            rule_name=rule_name,
            summary=summary,
            intent=intent,
            guidance=guidance,
            suggestion=suggestion,
            background=background,
            steps=steps,
            config_example=config_example,
            detection_example=detection_example,
        )
