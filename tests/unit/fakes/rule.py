"""Rule / MultiFileRule Protocol に適合するテスト用 Fake 実装"""

from paladin.lint import RuleMeta, SourceFile, SourceFiles, Violation


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
        violations: tuple[Violation, ...] = (),
    ) -> None:
        self._meta = RuleMeta(
            rule_id=rule_id,
            rule_name=rule_name,
            summary=summary,
            intent=intent,
            guidance=guidance,
            suggestion=suggestion,
        )
        self._violations = violations

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

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
        violations: tuple[Violation, ...] = (),
    ) -> None:
        self._meta = RuleMeta(
            rule_id=rule_id,
            rule_name=rule_name,
            summary=summary,
            intent=intent,
            guidance=guidance,
            suggestion=suggestion,
        )
        self._violations = violations

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_files: SourceFiles) -> tuple[Violation, ...]:
        """事前設定した違反リストを返す"""
        return self._violations
