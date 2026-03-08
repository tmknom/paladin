from datetime import datetime
from pathlib import Path

from example.transform.context import TransformContext


class TestTransformContext:
    """TransformContextクラスのテスト"""

    def test_init_正常系_属性が正しく保持されること(self):
        # Arrange
        target_file = Path("input.txt")
        tmp_dir = Path("/tmp/output")
        current_datetime = datetime(2024, 12, 26, 15, 30, 45)

        # Act
        context = TransformContext(
            target_file=target_file,
            tmp_dir=tmp_dir,
            current_datetime=current_datetime,
        )

        # Assert
        assert context.target_file == target_file
        assert context.tmp_dir == tmp_dir
        assert context.current_datetime == current_datetime
