from pathlib import Path

import pytest

from paladin.rule.no_third_party_import import (
    NoThirdPartyImportRule,
    ThirdPartyChecker,
    ThirdPartyImportDetector,
)
from paladin.rule.types import RuleMeta, SourceFiles
from tests.unit.test_rule.helpers import make_source_file, make_source_files

_STDLIB = frozenset({"os", "sys"})
_ROOT = ("myapp",)


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


class TestNoThirdPartyImportRuleCheck:
    """NoThirdPartyImportRule.check のテスト"""

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


class TestThirdPartyChecker:
    """ThirdPartyChecker のテスト"""

    def test_is_third_party_正常系_サードパーティはTrueを返すこと(self):
        assert ThirdPartyChecker.is_third_party("requests", _STDLIB, _ROOT) is True

    def test_is_third_party_正常系_標準ライブラリはFalseを返すこと(self):
        assert ThirdPartyChecker.is_third_party("os", _STDLIB, _ROOT) is False

    def test_is_third_party_正常系_ルートパッケージはFalseを返すこと(self):
        assert ThirdPartyChecker.is_third_party("myapp", _STDLIB, _ROOT) is False

    def test_is_allowed_path_正常系_許可ディレクトリ配下はTrueを返すこと(self):
        path = Path("src/foundation/http.py")
        allow_dirs = ("src/foundation/",)
        assert ThirdPartyChecker.is_allowed_path(path, allow_dirs) is True

    def test_is_allowed_path_正常系_許可ディレクトリ外はFalseを返すこと(self):
        path = Path("src/app/main.py")
        allow_dirs = ("src/foundation/",)
        assert ThirdPartyChecker.is_allowed_path(path, allow_dirs) is False


class TestThirdPartyImportDetector:
    """ThirdPartyImportDetector のテスト"""

    def test_detect_from_import_正常系_複数名で複数Violationを返すこと(self):
        source = "from requests import get, post\n"
        source_file = make_source_file(source, "src/app/main.py")
        source_files = make_source_files((source, "src/app/main.py"))
        rule = NoThirdPartyImportRule(allow_dirs=())
        rule.prepare(source_files)
        stmt = source_file.imports[0]
        result = ThirdPartyImportDetector.detect_from_import(stmt, source_file, rule.meta)
        assert len(result) == 2
        assert result[0].rule_id == "no-third-party-import"

    def test_detect_plain_import_正常系_Violationを返すこと(self):
        source = "import requests\n"
        source_file = make_source_file(source, "src/app/main.py")
        source_files = make_source_files((source, "src/app/main.py"))
        rule = NoThirdPartyImportRule(allow_dirs=())
        rule.prepare(source_files)
        stmt = source_file.imports[0]
        result = ThirdPartyImportDetector.detect_plain_import(
            stmt, "requests", source_file, rule.meta
        )
        assert result.rule_id == "no-third-party-import"
