# no-testing-test-code

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-testing-test-code |
| 対象 | 複数ファイル |

## 概要

`tests/` 配下で定義されたクラスや関数に対するテストコードの作成を禁止するルールです。テスト用コード（Fake クラス・ヘルパー関数など）が別のテストファイルからテストされている場合に違反を検出します。

## 背景と意図

TDD（テストファースト）で開発していると、実装よりも先にテストを書く習慣が身につきます。この習慣が行き過ぎると、`tests/` 配下に追加した Fake クラスやテストユーティリティに対して、反射的にテストを書いてしまうことがあります。

テスト用コードをテストすることには、以下の問題があります。

- **完全に無駄**: `tests/` 配下のコードはプロダクションコードの品質を保証するために書かれている。そのコードを保証するためにさらにテストを書くことに終わりはなく、実質的な価値をもたらさない
- **設計の問題を示すサイン**: テストが必要になるほど複雑なコードを `tests/` 配下に置いていること自体が誤りである。Fake クラスやヘルパーは十分にシンプルな設計を保つべきであり、それ自体をテストする必要があるなら、プロダクションコードへの移動を検討すべき
- **メンテナンスコストの増大**: テスト用コードのテストが存在すると、テストヘルパーを変更するたびにそのテストも更新しなければならず、本来のプロダクションコードのテストに割くべきリソースを消費する
- **テストの責務の逸脱**: `tests/` ディレクトリの責務は `src/` 配下のプロダクションコードの品質を保証することである。その責務から外れたテストはノイズとなり、テストスイート全体の意図を読み取りにくくする

Fake クラスやテストヘルパーが複雑になっているなら、それは設計の複雑さを反映しているサインです。その場合、テストヘルパーにテストを追加するのではなく、ヘルパーをシンプルに保つか、複雑なロジックをプロダクションコードに移動して適切にテストするのが正しいアプローチです。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `tests/` 配下のコード `{name}` に対するテストが定義されている |
| reason | テスト用コードをテストすることは無駄なメンテナンスコストを生む。テストが必要なほど複雑なコードを `tests/` 配下に置くべきではない |
| suggestion | `{name}` のテストを削除してください。テストが必要なほど複雑なら、そのロジックを `src/` 配下に移動することを検討してください |

## 検出パターン

### 違反コード

```python
# tests/fake/fs.py — テスト用 Fake クラス
class InMemoryFsReader:
    def __init__(self, content: str = "") -> None:
        self.content = content

    def read(self, file_path: Path) -> str:
        return self.content
```

```python
# tests/unit/test_fake/test_fs.py — 違反: Fake クラスへのテスト
from tests.unit.fake.fs import InMemoryFsReader

class TestInMemoryFsReader:
    def test_read_returns_content(self) -> None:  # 違反: tests/ 配下のクラスをテストしている
        reader = InMemoryFsReader(content="hello")
        assert reader.read(Path("any.txt")) == "hello"
```

### 準拠コード

```python
# tests/unit/test_check/test_orchestrator.py — 準拠: src/ 配下のコードをテスト
from paladin.check.orchestrator import CheckOrchestrator
from tests.unit.fake.fs import InMemoryFsReader  # Fake はテストのセットアップに使う

class TestCheckOrchestrator:
    def test_orchestrate(self) -> None:  # 準拠: プロダクションコードをテストしている
        reader = InMemoryFsReader(content="# code")
        orchestrator = CheckOrchestrator(reader=reader)
        ...
```

## 検出の補足

### 検出ロジック

- テストファイル（`test_` プレフィックスのファイル、または `tests/` 配下のファイル）において `tests/` 配下のモジュールからインポートされたシンボルがあるか確認する
- そのシンボルが `TestXxx` クラスや `test_xxx` 関数の中でテスト対象として参照されている場合に違反とする
- 具体的には、`from tests.xxx import Yyy` の形式でインポートし、そのクラスをテストクラス内で直接インスタンス化・呼び出している場合を検出する

### 対象外のパターン

以下は違反として報告しません。

- `tests/` 配下のモジュールを `import` しているが、テスト対象としてではなくセットアップ（テスト用の Fake やフィクスチャの構築）として使っている場合
- `conftest.py` でのフィクスチャ定義（テストインフラの構築であり、テスト対象ではない）

### 適用範囲

このルールはテストファイル（`tests/` 配下）のみに適用します。プロダクションコード（`src/` 配下）が `tests/` のコードをインポートすること自体は別のルールで禁止すべき問題です。

## 既存ツールとの関係

Ruff・Pylint・pytest のいずれも、テストファイル内でテスト対象が `tests/` 配下のコードであるかどうかを検出するルールは提供していません。「どのコードをテストするか」という設計上の判断は既存のリンターでは扱われていない領域であり、Paladin で独自に扱います。
