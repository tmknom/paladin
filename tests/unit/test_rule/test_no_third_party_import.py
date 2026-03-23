from pathlib import Path

from paladin.rule.no_third_party_import import NoThirdPartyImportRule
from paladin.rule.types import RuleMeta, SourceFiles
from tests.unit.test_rule.helpers import make_source_files


def _rule_with_prepare(
    source_files: SourceFiles, allow_dirs: tuple[str, ...] = ("src/foundation/",)
) -> NoThirdPartyImportRule:
    """prepare() を呼んで root_packages を自動導出したルールを返す"""
    rule = NoThirdPartyImportRule(allow_dirs=allow_dirs)
    rule.prepare(source_files)
    return rule


class TestNoThirdPartyImportRuleMeta:
    """NoThirdPartyImportRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoThirdPartyImportRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-third-party-import"
        assert result.rule_name == "No Third Party Import"
        assert (
            result.summary
            == "許可ディレクトリ以外でのサードパーティライブラリのインポートを禁止する"
        )
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""


class TestNoThirdPartyImportRuleAllowDirs:
    """NoThirdPartyImportRule の allow_dirs 設定のテスト"""

    def test_check_正常系_allow_dirs未設定の場合は全ファイルで違反を検出すること(self):
        # Arrange
        source_files = make_source_files(
            ("import requests\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=())

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1

    def test_check_正常系_許可ディレクトリ内のファイルは違反なしを返すこと(self):
        # Arrange
        source_files = make_source_files(
            ("import requests\n", "src/foundation/http.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_許可ディレクトリ外のplain_importで違反を返すこと(self):
        # Arrange
        source_files = make_source_files(
            ("import requests\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1

    def test_check_正常系_許可ディレクトリ外のfrom_importで違反を返すこと(self):
        # Arrange
        source_files = make_source_files(
            ("from requests import get\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反フィールド値が正しいこと_plain_import(self):
        # Arrange
        source_files = make_source_files(
            ("import requests\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("src/app/main.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-third-party-import"
        assert violation.rule_name == "No Third Party Import"
        assert "requests" in violation.message

    def test_check_正常系_違反フィールド値が正しいこと_from_import(self):
        # Arrange
        source_files = make_source_files(
            ("from requests import get\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("src/app/main.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-third-party-import"
        assert "requests" in violation.message
        assert "get" in violation.message

    def test_check_正常系_from_importで複数名をインポートした場合に名前ごとに違反を返すこと(self):
        # Arrange
        source_files = make_source_files(
            ("from requests import get, post\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 2


class TestNoThirdPartyImportRuleExclusions:
    """NoThirdPartyImportRule の除外パターンのテスト"""

    def test_check_正常系_標準ライブラリのimportは違反なしを返すこと(self):
        # Arrange
        source_files = make_source_files(
            ("import os\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_標準ライブラリのfrom_importは違反なしを返すこと(self):
        # Arrange
        source_files = make_source_files(
            ("from pathlib import Path\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_ルートパッケージのimportは違反なしを返すこと(self):
        # Arrange: src/myapp/ がルートパッケージとして自動導出される
        source_files = make_source_files(
            ("import myapp\n", "src/app/main.py"),
            ("x = 1\n", "src/myapp/core.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_ルートパッケージのfrom_importは違反なしを返すこと(self):
        # Arrange
        source_files = make_source_files(
            ("from myapp.utils import helper\n", "src/app/main.py"),
            ("x = 1\n", "src/myapp/utils.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_相対インポートは違反なしを返すこと(self):
        # Arrange
        source_files = make_source_files(
            ("from . import utils\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()


class TestNoThirdPartyImportRuleAllowDirNormalization:
    """NoThirdPartyImportRule の allow_dirs 末尾スラッシュ正規化のテスト"""

    def test_check_正常系_末尾スラッシュなしのallow_dirsが正規化されて機能すること(self):
        # Arrange: 末尾スラッシュなしで指定
        source_files = make_source_files(
            ("import requests\n", "src/foundation/http.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert: 末尾スラッシュなしでも src/foundation/ 配下として認識される
        assert result == ()

    def test_check_正常系_末尾スラッシュなしのallow_dirsで誤判定しないこと(self):
        # Arrange: "src/found" を allow_dirs に指定しても "src/foundation/" は許可されない
        source_files = make_source_files(
            ("import requests\n", "src/foundation/http.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/found",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert: "src/found/" には前方一致しないため違反
        assert len(result) == 1

    def test_check_正常系_複数のallow_dirsが機能すること(self):
        # Arrange: 2つの許可ディレクトリ
        source_files = make_source_files(
            ("import requests\n", "src/infra/client.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/", "src/infra/"))

        # Act
        result = rule.check(source_files.files[0])

        # Assert: src/infra/ が許可されているので違反なし
        assert result == ()


class TestNoThirdPartyImportRuleEdgeCases:
    """NoThirdPartyImportRule のエッジケースのテスト"""

    def test_check_エッジケース_空ファイルは空タプルを返すこと(self):
        # Arrange
        source_files = make_source_files(("", "src/app/main.py"))
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_エッジケース_importなしのファイルは空タプルを返すこと(self):
        # Arrange
        source_files = make_source_files(("x = 1\n", "src/app/main.py"))
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_エッジケース_サブモジュールのfrom_importで違反を返すこと(self):
        # Arrange: requests.auth.HTTPBasicAuth は requests のサブモジュール
        source_files = make_source_files(
            ("from requests.auth import HTTPBasicAuth\n", "src/app/main.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1
