"""違反フィクスチャ: テストクラス内にネストされたクラスを含む"""


class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""

    class TestOrchestrate:  # 違反: テストクラスがネストされている
        def test_正常系_レポートを返す(self) -> None:
            pass

    class TestEdgeCases:  # 違反: 別のネストクラス
        def test_正常系_空のファイルで空レポートを返す(self) -> None:
            pass
