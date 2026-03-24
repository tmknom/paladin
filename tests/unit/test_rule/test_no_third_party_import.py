from pathlib import Path

import pytest

from paladin.rule.no_third_party_import import NoThirdPartyImportRule
from paladin.rule.types import RuleMeta, SourceFiles, Violation
from tests.unit.test_rule.helpers import make_source_files


def _rule_with_prepare(
    source_files: SourceFiles, allow_dirs: tuple[str, ...] = ("src/foundation/",)
) -> NoThirdPartyImportRule:
    """prepare() を呼んで root_packages を自動導出したルールを返す"""
    rule = NoThirdPartyImportRule(allow_dirs=allow_dirs)
    rule.prepare(source_files)
    return rule


class TestNoThirdPartyImportRuleHelpers:
    """NoThirdPartyImportRule のヘルパーメソッドの直接テスト"""

    def test_check_from_import_正常系_サードパーティのfrom_importで違反リストを返すこと(self):
        # Arrange
        source_files = make_source_files(("from requests import get\n", "src/app/main.py"))
        rule = _rule_with_prepare(source_files)
        source_file = source_files.files[0]
        stmt = source_file.imports[0]

        # Act
        result = rule._check_from_import(stmt, source_file)  # type: ignore[reportPrivateUsage]

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Violation)

    def test_check_from_import_正常系_標準ライブラリのfrom_importで空リストを返すこと(self):
        # Arrange
        source_files = make_source_files(("from pathlib import Path\n", "src/app/main.py"))
        rule = _rule_with_prepare(source_files)
        source_file = source_files.files[0]
        stmt = source_file.imports[0]

        # Act
        result = rule._check_from_import(stmt, source_file)  # type: ignore[reportPrivateUsage]

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_check_plain_import_正常系_サードパーティのplain_importで違反リストを返すこと(self):
        # Arrange
        source_files = make_source_files(("import requests\n", "src/app/main.py"))
        rule = _rule_with_prepare(source_files)
        source_file = source_files.files[0]
        stmt = source_file.imports[0]

        # Act
        result = rule._check_plain_import(stmt, source_file)  # type: ignore[reportPrivateUsage]

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Violation)

    def test_check_plain_import_正常系_標準ライブラリのplain_importで空リストを返すこと(self):
        # Arrange
        source_files = make_source_files(("import os\n", "src/app/main.py"))
        rule = _rule_with_prepare(source_files)
        source_file = source_files.files[0]
        stmt = source_file.imports[0]

        # Act
        result = rule._check_plain_import(stmt, source_file)  # type: ignore[reportPrivateUsage]

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0


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


class TestNoThirdPartyImportRuleCheck:
    """NoThirdPartyImportRule.check のテスト"""

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

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("import os\n", id="標準ライブラリimport"),
            pytest.param("from pathlib import Path\n", id="標準ライブラリfrom_import"),
            pytest.param("from . import utils\n", id="相対インポート"),
            pytest.param("", id="空ファイル"),
            pytest.param("x = 1\n", id="importなし"),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str) -> None:
        # Arrange
        source_files = make_source_files((source, "src/app/main.py"))
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 0

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
        assert len(result) == 0

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
        assert len(result) == 0

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("import requests\n", id="許可ディレクトリ外のplain_import"),
            pytest.param("from requests import get\n", id="許可ディレクトリ外のfrom_import"),
            pytest.param(
                "from requests.auth import HTTPBasicAuth\n", id="サブモジュールのfrom_import"
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str) -> None:
        # Arrange
        source_files = make_source_files((source, "src/app/main.py"))
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1

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
        assert len(result) == 0

    def test_check_正常系_末尾スラッシュなしのallow_dirsが正規化されて機能すること(self):
        # Arrange: 末尾スラッシュなしで指定
        source_files = make_source_files(
            ("import requests\n", "src/foundation/http.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/foundation",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert: 末尾スラッシュなしでも src/foundation/ 配下として認識される
        assert len(result) == 0

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
        assert len(result) == 0
