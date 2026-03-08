"""pytest設定ファイルと共通フィクスチャ

テスト全体で使用される共通のモック、フィクスチャ、設定を定義します。
"""

import os
from pathlib import Path
from typing import Any

import pytest

from example.config.path import PathConfig


def pytest_configure(config: Any) -> None:
    """pytest設定フック: テスト実行前に環境変数を設定"""
    # テスト用の環境変数を設定（モジュールimport前に実行される）
    os.environ["LOG_LEVEL"] = "INFO"


# テストデータディレクトリ
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    """テストフィクスチャディレクトリのパス"""
    return FIXTURES_DIR


@pytest.fixture
def path_config(tmp_path: Path):
    """テスト用PathConfigフィクスチャ

    テスト環境用に設定されたPathConfigインスタンスを提供します。

    Args:
        tmp_path: pytestのtmp_pathフィクスチャ

    Returns:
        テスト用に設定されたPathConfigインスタンス
    """
    return PathConfig.from_base_dir(tmp_path)


@pytest.fixture(autouse=True)
def reset_mocks():
    """各テスト後にモックをリセット"""
    yield
    # テスト後のクリーンアップはpytestが自動で行うため、特別な処理は不要
