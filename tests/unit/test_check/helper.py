"""値オブジェクト生成ファクトリ"""

from pathlib import Path

from paladin.check.result import CheckResult
from paladin.check.types import TargetFiles
from paladin.rule import SourceFiles, Violation, Violations


class ViolationFactory:
    """テスト用 Violation 生成ファクトリ"""

    @staticmethod
    def make(  # paladin: ignore[max-function-parameter]
        file: str = "src/paladin/__init__.py",
        line: int = 1,
        column: int = 0,
        rule_id: str = "require-all-export",
        rule_name: str = "Require __all__ Export",
        message: str = "__init__.py に __all__ が定義されていない",
        reason: str = "__all__ が未定義の場合、パッケージの公開インタフェースが不明確になる",
        suggestion: str = "__all__ リストを定義し、公開するシンボルを明示的に列挙する",
    ) -> Violation:
        return Violation(
            file=Path(file),
            line=line,
            column=column,
            rule_id=rule_id,
            rule_name=rule_name,
            message=message,
            reason=reason,
            suggestion=suggestion,
        )


class CheckResultFactory:
    """テスト用 CheckResult 生成ファクトリ"""

    @staticmethod
    def make(violations: tuple[Violation, ...]) -> CheckResult:
        return CheckResult(
            target_files=TargetFiles(files=()),
            source_files=SourceFiles(files=()),
            violations=Violations(items=violations),
        )
