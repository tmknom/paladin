"""check パッケージ用の Fake 実装"""

from pathlib import Path

from paladin.check.rule.types import RuleMeta, Violation
from paladin.check.types import ParsedFile


class FakeRule:
    """Rule Protocol に適合するテスト用 Fake"""

    def __init__(
        self,
        rule_id: str = "fake-rule",
        rule_name: str = "Fake Rule",
        summary: str = "Fake summary",
        violations: tuple[Violation, ...] = (),
    ) -> None:
        self._meta = RuleMeta(rule_id=rule_id, rule_name=rule_name, summary=summary)
        self._violations = violations

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, parsed_file: ParsedFile) -> tuple[Violation, ...]:
        """事前設定した違反リストを返す"""
        return self._violations


class InMemoryFsReader:
    """TextFileSystemReaderProtocol の InMemory 実装"""

    def __init__(
        self,
        content: str = "",
        contents: dict[str, str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.content = content
        self.contents = contents
        self.error = error
        self.read_paths: list[Path] = []

    def read(self, file_path: Path) -> str:
        """ファイルを読み込む（InMemory実装）"""
        self.read_paths.append(file_path)
        if self.error is not None:
            raise self.error
        if self.contents is not None:
            return self.contents[str(file_path)]
        return self.content
