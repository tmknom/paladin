# no-private-attr-in-test

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-private-attr-in-test |
| 対象 | 単一ファイル |

## 概要

テストコード内でテスト対象オブジェクトのプライベート属性（`_` プレフィックス）に直接アクセスしているパターンを検出するルールです。テストは公開 API の振る舞いのみを検証し、内部の実装詳細にアクセスすべきではありません。

## 背景と意図

プライベート属性（`_` プレフィックス）は「このクラスの内部実装であり、外部から直接アクセスすることを想定していない」という設計上の意思表示です。テストコードからこれらにアクセスすることは、以下の問題を引き起こします。

- **リファクタリングの障害** — 外部から見た振る舞いが変わらないリファクタリング（内部キャッシュの名前変更、データ構造の変更）を行うたびにテストが壊れる
- **設計の誤検証** — 「内部状態がこうなっていること」を確認するテストは、「外部から見た振る舞い」を確認するテストではない。実装の詳細への依存が高まる
- **テストの脆弱性** — プライベート属性は実装者が自由に変更できる領域であり、それに依存したテストは常に壊れるリスクを持つ

テストは公開メソッドの戻り値・副作用（Fake の呼び出し記録フィールド等）のみを検証することで、リファクタリングに対して堅牢なテストになります。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | テストコード内でプライベート属性 `{attr_name}` に直接アクセスしています |
| reason | プライベート属性は実装の詳細です。リファクタリングのたびにテストが壊れます |
| suggestion | 公開メソッドの戻り値または Fake の呼び出し記録フィールドを通じて振る舞いを検証してください |

## 検出パターン

### 違反コード

```python
class TestAstParser:
    """AstParser クラスのテスト"""

    def test_正常系_キャッシュに結果が保存される(self) -> None:
        # Arrange
        parser = AstParser()
        source = "x = 1"
        # Act
        parser.parse(source)
        # Assert
        assert parser._cache["x = 1"] is not None  # 違反: private 属性への直接アクセス
```

```python
class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""

    def test_正常系_ルールが実行される(self) -> None:
        # Arrange
        orchestrator = CheckOrchestrator(rule_set=rule_set)
        # Act
        orchestrator.orchestrate(context)
        # Assert
        assert orchestrator._rule_set._executed  # 違反: ネストしたプライベート属性アクセス
```

### 準拠コード

```python
class TestAstParser:
    """AstParser クラスのテスト"""

    def test_正常系_parseが結果を返す(self) -> None:
        # Arrange
        parser = AstParser()
        source = "x = 1"
        # Act
        result = parser.parse(source)  # 準拠: 公開メソッドの戻り値を検証
        # Assert
        assert isinstance(result, ast.Module)
```

```python
class TestCheckOrchestrator:
    """CheckOrchestrator クラスのテスト"""

    def test_正常系_violationsを返す(self) -> None:
        # Arrange
        fake_rule = FakeRule(violations=(violation,))
        orchestrator = CheckOrchestrator(rule_set=RuleSet([fake_rule]))
        # Act
        report = orchestrator.orchestrate(context)
        # Assert
        assert report.violations == (violation,)  # 準拠: 公開 API の戻り値を検証
```

## 検出の補足

### 検出ロジック

1. 対象ファイルが `is_test_file`（`tests/` 配下）であることを確認する
2. AST を `ast.walk` で走査し、`ast.Attribute` ノードを収集する
3. `attr` が `_` で始まり `__` で始まらないもの（シングルアンダースコアプレフィックス）を対象とする
4. `value` が `ast.Name(id="self")` であるものは除外する（テストクラス自身のプライベート属性は問題ない）
5. 残りのアクセスを違反として報告する

### ダンダーメソッドの扱い

`__init__`、`__str__`、`__repr__` 等のダンダーメソッド（`__` で始まる）は対象外です。ダンダーメソッドは公開 API の一部として機能するため、アクセスを禁止しません。

### `self._` の除外

テストクラス自身の `self._helper` のようなプライベートヘルパーメソッド呼び出しは、テストクラス内部の実装であり問題ありません。`value` が `ast.Name` で `id == "self"` の場合は除外します。

### 適用範囲

`tests/` 配下のすべての `.py` ファイルを対象とします。

### 報告の粒度

違反のあるプライベート属性アクセスごとに1件の違反を報告します。違反の行番号はアクセス式の行番号とします。

## 既存ツールとの関係

Ruff には `SLF001`（`private-member-access`）がありますが、これはプロダクションコード全般でのプライベートメンバーアクセスを検出するルールであり、テストコードに限定したルールではありません。また、`self._` の除外など Paladin の規約に合わせた判定が必要なため、Paladin で独自に提供します。
