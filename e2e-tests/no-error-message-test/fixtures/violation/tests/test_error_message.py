"""違反フィクスチャ: 例外メッセージ文言テストのパターンを含む"""


class TestErrorMessage:
    def test_異常系_matchによる文言テスト(self) -> None:
        # Act & Assert
        with pytest.raises(ValueError, match="空文字列は無効です"):  # noqa: F821
            raise ValueError("空文字列は無効です")

    def test_異常系_str_exc_info_valueによる文言テスト(self) -> None:
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:  # noqa: F821
            raise ValueError("空文字列は無効です")
        assert "空文字列は無効です" in str(exc_info.value)
