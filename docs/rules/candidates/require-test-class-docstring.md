# require-test-class-docstring

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | require-test-class-docstring |
| 対象 | 単一ファイル |

## 概要

テストファイル内の `Test` プレフィックスを持つクラスに docstring が存在することを要求するルールです。テストクラスに docstring がない場合に違反を検出します。

## 背景と意図

テストクラスの docstring は「このクラスが何をテストしているか」を宣言する唯一の公式な手段です。テストクラス名（例: `TestCheckOrchestrator`）だけでは、以下の情報が不明なままになります。

- テスト対象が `CheckOrchestrator` クラス全体なのか、特定のメソッドなのか
- テストクラスが担当するシナリオ（正常系全般か、特定の機能か）
- 日本語のクラス名では伝わらないコンテキスト

1行の docstring（例: `"""CheckOrchestrator クラスのテスト"""`）を記述することで、テストクラスの目的が明確になり、コードレビュアーや後から読む開発者がテストファイルの構造を素早く把握できます。

docstring の存在を自動検出することで、最低限の記述水準を機械的に保証できます。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | テストクラス `{class_name}` に docstring がありません |
| reason | テストクラスの docstring がないと、何をテストしているクラスかが一目で判断できません |
| suggestion | クラス定義の直後に1行の docstring を追加してください（例: `"""{ClassName} クラスのテスト"""`） |

## 検出パターン

### 違反コード

```python
# tests/unit/test_check/test_orchestrator.py
class TestCheckOrchestrator:  # 違反: docstring がない
    def test_正常系_レポートを返す(self) -> None:
        # Arrange
        ...
        # Act
        ...
        # Assert
        ...
```

### 準拠コード

```python
# tests/unit/test_check/test_orchestrator.py
class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""  # 準拠: 1行の docstring がある

    def test_正常系_レポートを返す(self) -> None:
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
2. AST を走査して `ast.ClassDef` ノードを収集する
3. クラス名が `Test` で始まるものを対象とする
4. `class_node.body[0]` が `ast.Expr` であり、その値が `ast.Constant` かつ型が `str` である場合に docstring ありと判定する
5. 上記条件を満たさない場合に違反を報告する

### 適用範囲

`tests/` 配下のすべての `.py` ファイルを対象とします。クラス名が `Test` で始まるもののみを検査します。`conftest.py` 内のクラスも対象となりますが、通常 `conftest.py` にテストクラスは定義しません。

### 報告の粒度

docstring のないテストクラスごとに1件の違反を報告します。違反の行番号は `class` 文の行番号とします。

## 既存ツールとの関係

Ruff には `D101`（クラス docstring の欠如）がありますが、テストクラスはデフォルトで対象外になることが多く、また docstring スタイルの検査まで含む設定が必要です。

Paladin の `require-test-class-docstring` はテストクラスに限定した「docstring の存在有無」のみを検査するシンプルなルールとして位置づけます。
