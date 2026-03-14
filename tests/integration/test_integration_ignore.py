"""ファイル単位 ignore の統合テスト

ignore-file ディレクティブによる違反抑制を実ファイルシステムで検証する。
"""

from pathlib import Path

from paladin.check import CheckOrchestratorProvider
from paladin.check.context import CheckContext


class TestIntegrationIgnore:
    """ignore-file ディレクティブの統合テスト"""

    def test_check_正常系_ignore_fileで全ルール違反が無視されること(self, tmp_path: Path):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# paladin: ignore-file\nfrom foo import bar\n", encoding="utf-8")
        context = CheckContext(targets=(tmp_path,))

        # Act
        report = CheckOrchestratorProvider().provide().orchestrate(context)

        # Assert
        assert report.exit_code == 0

    def test_check_正常系_ignore_file_with_ruleで特定ルール違反のみ無視されること(
        self, tmp_path: Path
    ):
        # Arrange: require-all-export のみ ignore し、require-qualified-third-party は適用されたまま
        init_file = tmp_path / "__init__.py"
        init_file.write_text(
            "# paladin: ignore-file[require-all-export]\nfrom foo import bar\n",
            encoding="utf-8",
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        report = CheckOrchestratorProvider().provide().orchestrate(context)

        # Assert: require-all-export は除外されたが他のルール違反は残るため exit_code == 1
        assert report.exit_code == 1
        assert "require-all-export" not in report.text

    def test_check_正常系_ディレクティブなしで通常通りルール適用されること(self, tmp_path: Path):
        # Arrange
        init_file = tmp_path / "__init__.py"
        init_file.write_text("from foo import bar\n", encoding="utf-8")
        context = CheckContext(targets=(tmp_path,))

        # Act
        report = CheckOrchestratorProvider().provide().orchestrate(context)

        # Assert
        assert report.exit_code == 1
