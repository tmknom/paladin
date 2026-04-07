"""Rule / MultiFileRule / PreparableRule Protocol に適合するテスト用 Fake 実装"""

from paladin.rule import RuleMeta, SourceFile, SourceFiles, Violation


class FakeRule:
    """Rule Protocol に適合するテスト用 Fake"""

    def __init__(
        self,
        rule_id: str = "fake-rule",
        rule_name: str = "Fake Rule",
        summary: str = "Fake summary",
        intent: str = "Fake intent",
        guidance: str = "Fake guidance",
        suggestion: str = "Fake suggestion",
        background: str | None = None,
        steps: tuple[str, ...] | None = None,
        config_example: str | None = None,
        detection_example: str | None = None,
        violations: tuple[Violation, ...] = (),
    ) -> None:
        self._meta = RuleMeta(
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
        self._violations = violations

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """事前設定した違反リストを返す"""
        return self._violations


class FakePreparableRule:
    """Rule + PreparableRule Protocol に適合するテスト用 Fake"""

    def __init__(
        self,
        rule_id: str = "fake-preparable-rule",
        rule_name: str = "Fake Preparable Rule",
        summary: str = "Fake summary",
        intent: str = "Fake intent",
        guidance: str = "Fake guidance",
        suggestion: str = "Fake suggestion",
        background: str | None = None,
        steps: tuple[str, ...] | None = None,
        config_example: str | None = None,
        detection_example: str | None = None,
        violations: tuple[Violation, ...] = (),
    ) -> None:
        self._meta = RuleMeta(
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
        self._violations = violations
        self.prepare_called_with: SourceFiles | None = None

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def prepare(self, source_files: SourceFiles) -> None:
        """呼び出しを記録する"""
        self.prepare_called_with = source_files

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """事前設定した違反リストを返す"""
        return self._violations


class FakeMultiFileRule:
    """MultiFileRule Protocol に適合するテスト用 Fake"""

    def __init__(
        self,
        rule_id: str = "fake-multi-rule",
        rule_name: str = "Fake Multi Rule",
        summary: str = "Fake summary",
        intent: str = "Fake intent",
        guidance: str = "Fake guidance",
        suggestion: str = "Fake suggestion",
        background: str | None = None,
        steps: tuple[str, ...] | None = None,
        config_example: str | None = None,
        detection_example: str | None = None,
        violations: tuple[Violation, ...] = (),
    ) -> None:
        self._meta = RuleMeta(
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
        self._violations = violations

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_files: SourceFiles) -> tuple[Violation, ...]:
        """事前設定した違反リストを返す"""
        return self._violations
