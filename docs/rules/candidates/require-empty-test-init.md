# require-empty-test-init

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | require-empty-test-init |
| 対象 | 単一ファイル |

## 概要

`tests/` 配下のパッケージに存在する `__init__.py` が空ファイルであることを要求するルールです。テストパッケージの `__init__.py` に何らかのコードが記述されている場合に違反を検出します。

## 背景と意図

テストパッケージの `__init__.py` は、Python にそのディレクトリをパッケージとして認識させるための空のマーカーファイルです。このファイルにコードを記述することは、以下の問題を引き起こします。

- **テスト環境の汚染** — `__init__.py` に記述されたコードはパッケージのインポート時に実行されるため、テスト収集の副作用やグローバル状態の変化が発生する可能性がある
- **誤配置の発見** — テスト支援コード（フィクスチャ・Fake クラス等）を `__init__.py` に書くことは、適切な場所（`conftest.py`、`tests/fake/`）に配置すべきコードが誤った場所に置かれているサインである
- **不必要な依存** — テストパッケージのインポート時に余分なモジュールが読み込まれ、テスト起動コストが増大する

`__init__.py` は空のマーカーファイルとして維持し、テスト支援コードは適切な場所（`conftest.py`、`tests/fake/`、`tests/unit/test_<package>/fake.py`）に配置することで、テストコードの構造が明確になります。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | テストパッケージの `__init__.py` にコードが記述されています |
| reason | テストパッケージの `__init__.py` は空のマーカーファイルであるべきです。コードを記述するとパッケージのインポート時に意図しない副作用が発生する可能性があります |
| suggestion | `__init__.py` の内容を削除してください。フィクスチャは `conftest.py` へ、共有 Fake クラスは `tests/fake/` へ移動してください |

## 検出パターン

### 違反コード

```python
# tests/unit/__init__.py — コードが記述されている
import logging

logging.basicConfig(level=logging.DEBUG)
```

```python
# tests/unit/test_check/__init__.py — フィクスチャが誤配置されている
import pytest

@pytest.fixture
def sample_file():
    return "sample.py"
```

### 準拠コード

```python
# tests/unit/__init__.py — 空ファイル（コンテンツなし）
```

```python
# tests/unit/test_check/conftest.py — フィクスチャは conftest.py に配置
import pytest

@pytest.fixture
def sample_file():
    return "sample.py"
```

## 検出の補足

### 検出ロジック

1. 対象ファイルが `is_test_file`（`tests/` 配下）かつ `is_init_py`（ファイル名が `__init__.py`）であることを確認する
2. `source.strip()` が空文字列でなければ違反を報告する

空白文字のみのファイルは空ファイルとして扱い、違反として報告しません。

### 適用範囲

`tests/` 配下のすべての `__init__.py` を対象とします。プロダクションコード（`src/` 配下）の `__init__.py` は対象外です。

### 報告の粒度

違反はファイルにつき1件を報告します。行番号は1行目とします。

## 既存ツールとの関係

Ruff・Pylint ともに `tests/` 配下の `__init__.py` が空であることを強制するルールは持っていません。これはプロジェクト固有の設計規約であり、Paladin で独自に提供します。
