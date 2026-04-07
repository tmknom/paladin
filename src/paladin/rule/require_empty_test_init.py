"""Rule 層の単一ファイルルール。テストパッケージの __init__.py をマーカーファイルに限定する。

仕様は docs/rules/require-empty-test-init.md を参照。
"""

from paladin.rule.types import RuleMeta, SourceFile, Violation

_MESSAGE = "テストパッケージの `__init__.py` にコードが記述されています"
_REASON = (
    "テストパッケージの `__init__.py` は空のマーカーファイルであるべきです。"
    "コードを記述するとパッケージのインポート時に意図しない副作用が発生する可能性があります"
)
_SUGGESTION = (
    "`__init__.py` の内容を削除してください。"
    "フィクスチャは `conftest.py` へ、共有 Fake クラスは `tests/fake/` へ移動してください"
)


class RequireEmptyTestInitRule:
    """テストパッケージの __init__.py が空ファイルであることを要求するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="require-empty-test-init",
            rule_name="Require Empty Test Init",
            summary="テストパッケージの `__init__.py` が空であることを要求する",
            intent="テストパッケージの `__init__.py` をマーカーファイルに限定し、意図しない副作用を防止する",
            guidance="`tests/` 配下の `__init__.py` にコードが記述されていないか確認する",
            suggestion=_SUGGESTION,
            background="テストパッケージの __init__.py は Python にそのディレクトリをパッケージとして認識させるための空のマーカーファイルです。コードを記述するとパッケージのインポート時に実行されテスト環境を汚染したり、誤配置のサインとなります。",
            steps=(
                "__init__.py の内容を削除して空ファイルにする",
                "フィクスチャは conftest.py へ移動する",
                "共有 Fake クラスは tests/fake/ へ移動する",
            ),
            detection_example="# 違反: テストパッケージの __init__.py にコードがある\n# tests/unit/__init__.py\nimport logging\nlogging.basicConfig(level=logging.DEBUG)  # 違反\n\n# 準拠: __init__.py は空ファイル\n# tests/unit/__init__.py（空）",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う。

        Flow:
            1. テストファイルでなければスキップ
            2. `__init__.py` でなければスキップ
            3. 内容が空ならスキップ
            4. 違反を生成して返す
        """
        if not source_file.is_test_file:
            return ()
        if not source_file.is_init_py:
            return ()
        if source_file.source.strip() == "":
            return ()
        violation = self._meta.create_violation_at(
            location=source_file.location(line=1),
            message=_MESSAGE,
            reason=_REASON,
            suggestion=_SUGGESTION,
        )
        return (violation,)
