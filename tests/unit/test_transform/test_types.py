import json

from example.transform.types import DstText, SrcText, TransformResult


class TestTransformResult:
    """TransformResultクラスのテスト"""

    def test_to_json_正常系_JSON文字列を返すこと(self):
        # Arrange
        result = TransformResult(src_length=3, dst_length=4)

        # Act
        json_str = result.to_json()

        # Assert
        data = json.loads(json_str)
        assert data["src_length"] == 3
        assert data["dst_length"] == 4


class TestSrcText:
    """SrcTextクラスのテスト"""

    def test_numbered_lines_正常系_複数行テキストに行番号を付与(self):
        # Arrange
        src = SrcText("first\nsecond\nthird")

        # Act
        result = src.numbered_lines()

        # Assert
        assert result == ["1: first", "2: second", "3: third"]

    def test_numbered_lines_正常系_空テキストは空リストを返す(self):
        # Arrange
        src = SrcText("")

        # Act
        result = src.numbered_lines()

        # Assert
        assert result == []

    def test_length_正常系_行数を返す(self):
        # Arrange
        src = SrcText("line1\nline2\nline3")

        # Act
        result = src.length()

        # Assert
        assert result == 3


class TestDstText:
    """DstTextクラスのテスト"""

    def test_length_正常系_行数を返す(self):
        # Arrange
        dst = DstText("line1\nline2\nline3")

        # Act
        result = dst.length()

        # Assert
        assert result == 3

    def test_str_正常系_内部テキストを文字列として返す(self):
        # Arrange
        dst = DstText("hello\nworld")

        # Act
        result = str(dst)

        # Assert
        assert result == "hello\nworld"
