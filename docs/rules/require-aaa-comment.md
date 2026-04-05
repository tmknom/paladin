# require-aaa-comment

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | require-aaa-comment |
| 対象 | 単一ファイル |

## 概要

テストメソッド内に `# Arrange`、`# Act`、`# Assert` のコメントが存在することを要求するルールです。`# Act` または `# Act & Assert` コメントが欠如している場合に違反を検出します。

## 背景と意図

AAA（Arrange-Act-Assert）パターンはテストの構造を3つのフェーズに分けることで、テストの読みやすさと保守性を高めます。

- **Arrange** — テスト対象を動かすための前提条件を準備する
- **Act** — テスト対象のメソッドや処理を実行する
- **Assert** — 実行結果を検証する

このパターンをコメントで明示することで、以下の効果があります。

- **境界の可視化** — テストの「準備」「実行」「検証」がどこで切り替わるかが一目で分かる
- **設計の強制** — コメントが必要になることで、「何を準備し、何を実行し、何を検証するか」をテストを書く前に考えるようになる
- **レビューの容易化** — Act の箇所を見れば「何をテストしているか」が即座に分かり、Assert の箇所を見れば「何を期待しているか」が分かる

コメントの存在を自動検出することで、AAA パターンの徹底を機械的に保証できます。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | テストメソッド `{method_name}` に `# Act` コメントがありません |
| reason | AAA パターンのコメントがないと、テストの「実行」フェーズの境界が不明確になります |
| suggestion | `# Arrange`、`# Act`、`# Assert` コメントを追加してください。Act と Assert が同時の場合は `# Act & Assert` を使用してください |

## 検出パターン

### 違反コード

```python
class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""

    def test_正常系_レポートを返す(self) -> None:  # 違反: AAA コメントがない
        source_files = SourceFiles((...,))
        report = orchestrator.orchestrate(context)
        assert report.violations == ()
```

```python
    def test_正常系_レポートを返す(self) -> None:  # 違反: # Act がない
        # Arrange
        source_files = SourceFiles((...,))
        # なんらかのコメント
        report = orchestrator.orchestrate(context)
        assert report.violations == ()
```

### 準拠コード

```python
class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""

    def test_正常系_レポートを返す(self) -> None:  # 準拠: # Act & Assert
        # Arrange
        source_files = SourceFiles((...,))
        # Act
        report = orchestrator.orchestrate(context)
        # Assert
        assert report.violations == ()
```

```python
    def test_正常系_例外が発生する(self) -> None:  # 準拠: # Act & Assert の省略形
        # Arrange
        invalid_path = Path("/nonexistent")
        # Act & Assert
        with pytest.raises(ValueError):
            orchestrator.orchestrate(context)
```

```python
    def test_正常系_空のレポートを返す(self) -> None:  # 準拠: Arrange 省略（前提条件なし）
        # Act
        report = orchestrator.orchestrate(empty_context)
        # Assert
        assert report.violations == ()
```

## 検出の補足

### 検出ロジック

1. 対象ファイルが `is_test_file`（`tests/` 配下）であることを確認する
2. AST を走査して `ast.FunctionDef` ノードを収集する
3. メソッド名が `test_` で始まるものを対象とする
4. メソッドの本文に含まれるソース行を走査し、以下のいずれかが存在するかを確認する
    - `# Act` を含む行
    - `# Act & Assert` を含む行
5. 上記コメントが存在しない場合に違反を報告する

### コメントの検出方法

AST のコメントノードは存在しないため、ソーステキストからメソッド本文の行範囲（`func_node.lineno` から `func_node.end_lineno`）を取得し、各行に `# Act` または `# Act & Assert` が含まれるかを文字列マッチングで確認します。

### Arrange の省略ルール

`# Arrange` コメントは省略可能です。テストメソッドに前提条件の準備コードがない場合（Act のみ、または Act & Assert のみ）、`# Arrange` を書かずに `# Act` から始めることが許容されます。したがって、`# Act` の存在のみを必須チェックの対象とします。

### Assert の扱い

`# Act & Assert` が存在する場合、`# Assert` は省略できます。`# Act` のみが存在し `# Assert` が存在しない場合も許容します（Act の直後の assert が暗黙的な Assert として機能するため）。

### 適用範囲

`tests/` 配下のすべての `.py` ファイルを対象とします。メソッド名が `test_` で始まるもののみを検査します。

### 報告の粒度

違反のあるテストメソッドごとに1件の違反を報告します。違反の行番号は `def` 文の行番号とします。

## 既存ツールとの関係

Ruff・Pylint ともに AAA コメントの存在を強制するルールは持っていません。これはテストコードの構造規約であり、Paladin で独自に提供します。
