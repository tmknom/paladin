# no-frozen-instance-test

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-frozen-instance-test |
| 対象 | 単一ファイル |

## 概要

テストファイル内で `dataclasses.FrozenInstanceError` を `pytest.raises` でキャッチするテストを禁止するルールです。frozen dataclass の不変性は型チェッカーが静的に保証するものであり、ランタイムテストで重複検証する必要はありません。

## 背景と意図

`@dataclass(frozen=True)` で定義されたクラスのインスタンス属性への代入は、pyright などの型チェッカーが静的に検出します。

```python
data.id = "new_value"  # pyright: Cannot assign to attribute "id" for class "Data"
```

この静的検査が有効な状態で、さらにランタイムテストとして `FrozenInstanceError` の発生を確認することは、以下の問題を引き起こします。

- **二重検証の無駄** — 型チェッカーが CI で検出できる内容をテストで再確認しても、保護の強度は変わらない
- **テストの肥大化** — 設計上の性質（frozen であること）は型定義で表現されており、それをテストで再確認することはテストの役割を超えている
- **メンテナンスコスト** — frozen を外した場合、このテストは失敗するが、型チェッカーも同時に警告を出すため、テストの存在価値がない

pyright で保証される内容はテストの対象外とすることで、テストを本当に必要なビジネスロジックの検証に集中させます。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `FrozenInstanceError` のテストは不要です |
| reason | `frozen=True` の不変性は pyright が静的に検証します。ランタイムテストで重複検証する必要はありません |
| suggestion | このテストを削除してください。不変性の保証は pyright に委ねてください |

## 検出パターン

### 違反コード

```python
import dataclasses
import pytest

class TestSourceFile:
    """SourceFile クラスのテスト"""

    def test_異常系_frozen属性への代入で例外が発生する(self) -> None:
        # Arrange
        source_file = SourceFile(file_path=Path("foo.py"), tree=ast.parse(""), source="")
        # Act & Assert
        with pytest.raises(dataclasses.FrozenInstanceError):  # 違反: frozen 不変性テスト
            source_file.file_path = Path("bar.py")  # type: ignore
```

```python
    def test_異常系_frozen属性への代入で例外が発生する(self) -> None:
        # Arrange
        source_file = SourceFile(file_path=Path("foo.py"), tree=ast.parse(""), source="")
        # Act & Assert
        with pytest.raises(FrozenInstanceError):  # 違反: import して使っている場合も検出
            source_file.file_path = Path("bar.py")
```

### 準拠コード

```python
class TestSourceFile:
    """SourceFile クラスのテスト"""

    def test_正常系_file_pathを取得できる(self) -> None:  # 準拠: 公開 API の振る舞いをテスト
        # Arrange
        path = Path("foo.py")
        # Act
        source_file = SourceFile(file_path=path, tree=ast.parse(""), source="")
        # Assert
        assert source_file.file_path == path
```

## 検出の補足

### 検出ロジック

1. 対象ファイルが `is_test_file`（`tests/` 配下）であることを確認する
2. AST を `ast.walk` で走査し、`ast.Call` ノードを収集する
3. `pytest.raises(...)` の呼び出しパターンを検出する
    - `func` が `ast.Attribute` で `value.id == "pytest"` かつ `attr == "raises"`
4. 第1引数（`args[0]`）が以下のいずれかに該当する場合に違反を報告する
    - `ast.Attribute` で `attr == "FrozenInstanceError"`（`dataclasses.FrozenInstanceError`）
    - `ast.Name` で `id == "FrozenInstanceError"`（`from dataclasses import FrozenInstanceError`）

### 適用範囲

`tests/` 配下のすべての `.py` ファイルを対象とします。

### 報告の粒度

違反のある `pytest.raises` 呼び出しごとに1件の違反を報告します。違反の行番号は `pytest.raises` 呼び出しの行番号とします。

## 既存ツールとの関係

Ruff・Pylint ともに `FrozenInstanceError` のテストを禁止するルールは持っていません。これは「型チェッカーが保証する内容をランタイムテストで重複検証しない」という設計原則に基づく規約であり、Paladin で独自に提供します。
