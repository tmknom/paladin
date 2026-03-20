"""pytest設定ファイルと共通フィクスチャ

テスト全体で使用される共通のモック、フィクスチャ、設定を定義します。
"""

import os
from typing import Any

import pytest


def pytest_configure(config: Any) -> None:
    """pytest設定フック: テスト実行前に環境変数を設定"""
    # テスト用の環境変数を設定（モジュールimport前に実行される）
    os.environ["LOG_LEVEL"] = "INFO"


@pytest.fixture(autouse=True)
def reset_mocks():
    """各テスト後にモックをリセット"""
    yield
    # テスト後のクリーンアップはpytestが自動で行うため、特別な処理は不要
