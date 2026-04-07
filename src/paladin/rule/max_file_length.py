"""ファイルの最大行数制限ルール"""

from paladin.rule.types import RuleMeta, SourceFile, Violation

_DEFAULT_MAX_LINES = 300
_DEFAULT_MAX_TEST_LINES = 500


class FileLengthCalculator:
    """ファイルの行数を計算するクラス"""

    @staticmethod
    def calc(source: str) -> int:
        """ファイルの行数を返す"""
        if not source:
            return 0
        return len(source.splitlines())


class FileLengthDetector:
    """ファイル行数の閾値判定と Violation 生成を行う"""

    @staticmethod
    def detect(
        source_file: SourceFile,
        length: int,
        limit: int,
        meta: RuleMeta,
    ) -> Violation | None:
        """Length が limit を超えていれば Violation を返す。そうでなければ None を返す"""
        if length <= limit:
            return None
        file_path = source_file.file_path.name
        message = f"ファイル `{file_path}` は `{length}` 行です。上限は `{limit}` 行です"
        if source_file.is_test_file:
            suggestion = "parametrize やフィクスチャで重複を排除し、必要に応じてテストファイルを分割してください"
        else:
            suggestion = "不要なコードを削除し、クラスや関数の責務を見直したうえで、必要に応じてファイルを分割してください"
        return meta.create_violation_at(
            location=source_file.location(length),
            message=message,
            reason="ファイルが長すぎることは、責務の肥大化や設計上の問題を示す兆候です",
            suggestion=suggestion,
        )


class MaxFileLengthRule:
    """ファイルの行数が設定された上限を超えた場合に違反を検出するルール"""

    def __init__(
        self, max_lines: int = _DEFAULT_MAX_LINES, max_test_lines: int = _DEFAULT_MAX_TEST_LINES
    ) -> None:
        """ルールを初期化する"""
        self._max_lines = max_lines
        self._max_test_lines = max_test_lines
        self._meta = RuleMeta(
            rule_id="max-file-length",
            rule_name="Max File Length",
            summary="単一ファイルの行数が設定された上限を超えた場合に違反を検出する",
            intent="ファイルの肥大化を防ぎ、単一責任原則を促進する",
            guidance="各ファイルの行数を確認し、上限を超えていないか検査する",
            suggestion="不要なコードを削除し、責務を見直したうえで、必要に応じてファイルを分割してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        limit = self._max_test_lines if source_file.is_test_file else self._max_lines
        length = FileLengthCalculator.calc(source_file.source)
        violation = FileLengthDetector.detect(source_file, length, limit, self._meta)
        if violation is None:
            return ()
        return (violation,)
