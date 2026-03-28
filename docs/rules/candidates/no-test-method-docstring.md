# no-test-method-docstring

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-test-method-docstring |
| 対象 | 単一ファイル |

## 概要

テストファイル内の `test_` プレフィックスを持つメソッドに docstring が記述されている場合に違反を検出するルールです。テストメソッドに docstring は不要であり、その存在は情報の二重管理を示します。

## 背景と意図

テストメソッド名は `test_<対象メソッド>_<系統>_<期待する振る舞い>` の形式で、テストの目的が自己説明的になるよう設計されます。この命名規則が守られていれば、docstring は不要な重複情報になります。

テストメソッドに docstring を書くことは、以下の問題を引き起こします。

- **二重管理の発生** — テストメソッド名と docstring の内容が乖離したとき（例: メソッド名を変更したが docstring は古いまま）、読み手を混乱させる
- **命名規則の形骸化** — docstring で補足できると考えることで、メソッド名が不明瞭になるインセンティブが生じる。「名前で自明にする」という原則が崩れる
- **コードの肥大化** — テストメソッド数が多いほど、docstring による冗長な記述がファイルを膨らませ、本質的な Arrange/Act/Assert の可読性が下がる

テストメソッド名で意図を完全に表現し、docstring を一切書かないことで、テスト名が設計の一部として機能します。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | テストメソッド `{method_name}` に docstring が記述されています |
| reason | テストメソッドの目的はメソッド名で表現します。docstring があると名前との二重管理が発生します |
| suggestion | docstring を削除し、テストの目的がメソッド名だけで伝わるよう名前を改善してください |

## 検出パターン

### 違反コード

```python
class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""

    def test_正常系_violationsを返す(self) -> None:
        """正常にファイルを解析し、違反を返すことを確認する"""  # 違反: docstring が不要
        # Arrange
        ...
        # Act
        ...
        # Assert
        ...
```

### 準拠コード

```python
class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""

    def test_正常系_violationsを返す(self) -> None:  # 準拠: docstring なし
        # Arrange
        ...
        # Act
        ...
        # Assert
        ...
```

## 検出の補足

### 検出ロジック

1. 対象ファイルが `is_test_file`（`tests/` 配下）であることを確認する
2. AST を走査して `ast.FunctionDef` ノードを収集する
3. メソッド名が `test_` で始まるものを対象とする
4. `func_node.body[0]` が `ast.Expr` であり、その値が `ast.Constant` かつ型が `str` である場合に docstring ありと判定し、違反を報告する

### 適用範囲

`tests/` 配下のすべての `.py` ファイルを対象とします。メソッド名が `test_` で始まるもののみを検査します。`setUp` / `tearDown` 等の pytest フック、`conftest.py` のフィクスチャ関数は対象外です。

### 報告の粒度

docstring のあるテストメソッドごとに1件の違反を報告します。違反の行番号は `def` 文の行番号とします。

## 既存ツールとの関係

Ruff には `D102`（メソッド docstring の欠如）はありますが、「docstring がある場合に違反」というルールは持っていません。テストメソッドの docstring 禁止はプロジェクトの命名規則に基づく設計規約であり、Paladin で独自に提供します。
