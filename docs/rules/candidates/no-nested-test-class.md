# no-nested-test-class

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-nested-test-class |
| 対象 | 単一ファイル |

## 概要

テストファイル内で、テストクラスの中に別のクラスが定義されているネスト構造を禁止するルールです。テストクラスの `body` 内に `ClassDef` が存在する場合に違反を検出します。

## 背景と意図

テストクラスのネストは、pytest のネストクラスサポートを利用してテストを「グループ化」する手法として使われることがあります。しかし、この構造は以下の問題を引き起こします。

- **可読性の低下** — テストファイルを読む際、どのクラスがどのテストクラスに属するかをインデント構造で追わなければならず、認知負荷が増大する
- **pytest との摩擦** — pytest はネストされたクラスをテストクラスとして発見するが、ネストの深さによってはフィクスチャのスコープや継承関係が複雑になる
- **フラット構造の放棄** — テストクラスをフラットに並べれば済む構造をわざわざネストにすることで、テストファイルの構造が不必要に複雑になる
- **代替手段の存在** — テストのグループ化はファイルの分割や命名規則（`TestMyClassCreate`, `TestMyClassValidate`）で表現でき、ネストは不要である

テストクラスはフラットな構造にすることで、テストの所在が一目で把握でき、pytest との統合も単純になります。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | テストクラス `{outer_class}` の中にクラス `{inner_class}` がネストされています |
| reason | テストクラスのネストは可読性を下げます。テストはフラットな構造に保ってください |
| suggestion | ネストされたクラスをトップレベルのテストクラスとして独立させてください |

## 検出パターン

### 違反コード

```python
# tests/unit/test_check/test_orchestrator.py
class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""

    class TestOrchestrate:  # 違反: テストクラスがネストされている
        def test_正常系_レポートを返す(self) -> None:
            # ...
            pass

    class TestEdgeCases:  # 違反: 別のネストクラス
        def test_正常系_空のファイルで空レポートを返す(self) -> None:
            # ...
            pass
```

### 準拠コード

```python
# tests/unit/test_check/test_orchestrator.py — フラットな構造
class TestCheckOrchestratorOrchestrate:
    """CheckOrchestrator.orchestrate メソッドのテスト"""

    def test_正常系_レポートを返す(self) -> None:
        # ...
        pass


class TestCheckOrchestratorEdgeCases:
    """CheckOrchestrator のエッジケースのテスト"""

    def test_正常系_空のファイルで空レポートを返す(self) -> None:
        # ...
        pass
```

## 検出の補足

### 検出ロジック

1. 対象ファイルが `is_test_file`（`tests/` 配下）であることを確認する
2. AST の `tree.body` からトップレベルの `ast.ClassDef` を走査する
3. 各クラスの `body` 内に `ast.ClassDef` が存在する場合、ネストされたクラスとして違反を報告する
4. ネストの深さにかかわらず、任意のクラス定義が存在すれば違反とする

### 内部クラスとの区別

検査対象はテストファイル内のすべての `ClassDef` ネストです。ネストされたクラスが `Test` プレフィックスを持つかどうかにかかわらず、テストクラス内のクラス定義を検出します。テストクラス内にヘルパークラスを定義するパターンも不適切であり、`tests/fake/` や `tests/unit/test_<package>/fake.py` に移動すべきです。

### 適用範囲

`tests/` 配下のすべての `.py` ファイルを対象とします。

### 報告の粒度

ネストされたクラスごとに1件の違反を報告します。違反の行番号はネストされた `class` 文の行番号とします。

## 既存ツールとの関係

Ruff・Pylint ともにテストクラスのネストを禁止するルールは持っていません。これはテスト設計の規約であり、Paladin で独自に提供します。
