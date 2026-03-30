"""pytest設定ファイルと共通フィクスチャ

テスト全体で使用される共通のフィクスチャ、設定を定義します。
"""

import os


# pytest_configure は pytest が自動的に呼び出すフック関数。
# conftest.py にこの名前で定義するだけで、テスト収集・実行前に pytest が検知して実行する。
# 明示的な呼び出しコードは存在しないが、デッドコードではない。
def pytest_configure() -> None:
    """pytest設定フック: テスト実行前に環境変数を設定"""
    os.environ["EXAMPLE_LOG_LEVEL"] = "WARNING"
