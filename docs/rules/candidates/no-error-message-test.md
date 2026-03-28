# no-error-message-test

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-error-message-test |
| 対象 | 単一ファイル |

## 概要

テストファイル内で例外メッセージの文言を検証しているパターンを検出するルールです。`pytest.raises(match=...)` の使用、または `exc_info.value` を文字列に変換して比較しているコードを違反として報告します。

## 背景と意図

例外が発生することを確認するテストでは、「どの型の例外が発生するか」を検証すれば十分です。例外メッセージの文言は実装の詳細であり、以下の問題を引き起こします。

- **文言変更のたびにテストが壊れる** — エラーメッセージの改善（より分かりやすい表現への変更、誤字修正、多言語対応）があるたびに、機能的には正しいコードに対してテストが失敗する
- **テストが意図と乖離する** — 「この操作が失敗すること」を確認したいのに、「このメッセージが含まれること」を確認するテストになり、テストの意図が実装の詳細に侵食される
- **リファクタリングの障害** — 内部のエラーメッセージ生成ロジックを改善したいとき、テストが足かせになる

例外テストでは例外の型のみを検証し、メッセージ文言の検証を禁止することで、テストが「何が起きるか」を確認し「どのように報告するか」という実装の詳細から切り離されます。

## 診断メッセージ

### `pytest.raises(match=...)` を使用している場合

| フィールド | 内容 |
|-----------|------|
| message | `pytest.raises` に `match` 引数が指定されています |
| reason | 例外メッセージの文言は実装の詳細です。文言の変更のたびにテストが壊れます |
| suggestion | `match` 引数を削除してください。例外の型のみを検証してください |

### `exc_info.value` を文字列比較している場合

| フィールド | 内容 |
|-----------|------|
| message | 例外メッセージの文言を文字列で検証しています |
| reason | 例外メッセージの文言は実装の詳細です。文言の変更のたびにテストが壊れます |
| suggestion | `str(exc_info.value)` による文字列比較を削除してください。例外の型のみを検証してください |

## 検出パターン

### 違反コード

```python
# 違反パターン1: match= 引数による文言テスト
def test_異常系_無効な値でValueErrorが発生する(self) -> None:
    # Arrange
    invalid_value = ""
    # Act & Assert
    with pytest.raises(ValueError, match="空文字列は無効です"):  # 違反: match による文言テスト
        validate(invalid_value)
```

```python
# 違反パターン2: exc_info.value の文字列比較
def test_異常系_無効な値でValueErrorが発生する(self) -> None:
    # Arrange
    invalid_value = ""
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        validate(invalid_value)
    assert "空文字列は無効です" in str(exc_info.value)  # 違反: 文言の文字列比較
```

```python
# 違反パターン3: match= に正規表現を使った場合も違反
    with pytest.raises(ValueError, match=r"無効.*値"):  # 違反
        validate(invalid_value)
```

### 準拠コード

```python
# 準拠: 例外の型のみを検証する
def test_異常系_無効な値でValueErrorが発生する(self) -> None:
    # Arrange
    invalid_value = ""
    # Act & Assert
    with pytest.raises(ValueError):  # 準拠: 例外の型のみ
        validate(invalid_value)
```

## 検出の補足

### 検出ロジック

**パターン1: `pytest.raises(match=...)` の検出**

1. 対象ファイルが `is_test_file`（`tests/` 配下）であることを確認する
2. AST を `ast.walk` で走査し、`ast.Call` ノードを収集する
3. `pytest.raises(...)` の呼び出しパターンを検出する
    - `func` が `ast.Attribute` で `value.id == "pytest"` かつ `attr == "raises"`
4. `keywords` に `arg == "match"` のキーワード引数が存在する場合に違反を報告する

**パターン2: `str(exc_info.value)` の文字列比較の検出**

1. テストファイル内の `ast.Call` ノードを走査する
2. `str(...)` 呼び出しで引数が `ast.Attribute` かつ `attr == "value"` のパターンを検出する
3. その `value.value` の属性が `exc_info` / `exc` に相当する名前を持つ場合に違反を報告する

### 適用範囲

`tests/` 配下のすべての `.py` ファイルを対象とします。

### 報告の粒度

違反パターンごとに1件の違反を報告します。`pytest.raises(match=...)` はその `Call` ノードの行番号、`str(exc_info.value)` はその式の行番号とします。

## 既存ツールとの関係

Ruff・Pylint ともに例外メッセージ文言テストを禁止するルールは持っていません。これは「実装の詳細をテストしない」という設計原則に基づく規約であり、Paladin で独自に提供します。
