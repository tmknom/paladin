# Pythonテスト設計

本プロジェクトのPythonテストコードにおける設計原則・構造・パターンを示す。

## テストの種類と配置

本プロジェクトはユニットテストとインテグレーションテストの2種類を使い分ける。

| 種類 | 配置先 | 実行コマンド | スコープ | 外部依存 |
|------|--------|------------|--------|--------|
| ユニットテスト | `tests/unit/` | `make test-unit` | 単一クラス・関数の振る舞い | Fake で完全に分離する |
| インテグレーションテスト | `tests/integration/` | `make test-integration` | CLI から結果出力までのエンドツーエンド | 外部ネットワークのみ分離する |
| E2Eテスト | `e2e-tests/` | `make test-e2e` | ルール仕様と実装の一致検証 | 静的 Fixture ファイルのみ使用する |

`tests/unit/` の内部構造はプロダクションコードのパッケージ構成をミラーリングする。
対応するプロダクションパッケージに `test_` プレフィックスを付けたディレクトリ名を使う。

```
src/xxx/feature/          →  tests/unit/test_feature/
src/xxx/config/         →  tests/unit/test_config/
src/xxx/foundation/fs/  →  tests/unit/test_foundation/test_fs/
```

## テスト設計の原則

### Fake によるテスト分離

ユニットテストでは Mock を原則として使わない。
代わりに Protocol に適合する、具象クラス（Fake）で外部依存を分離する。

### Protocol との連携

Fake は Protocol の Structural Subtyping を利用する。
Protocol に明示的に継承しなくても、メソッドシグネチャが一致していれば準拠できる。
これにより、Fake をプロダクションコードに依存させずに独立して管理できる。

### AAA（Arrange-Act-Assert）パターン

すべてのテストメソッドは AAA パターンで構造化する。

```python
def test_xxx(self):
    # Arrange
    ...

    # Act
    result = ...

    # Assert
    assert ...
```

`# Arrange`、`# Act`、`# Assert` のコメントを付ける。
Arrange コードがない場合は `# Arrange` を省略できる。
Act と Assert を分離できない場合は `# Act & Assert` を使う。
補足が必要な場合はコメントを追記する。

### テスト責務の原則

各パッケージのテストは自身の責務範囲のみを検証する。

- 別パッケージで発生する例外やエラーハンドリングは、そのパッケージのテストに任せる
- 別パッケージの Protocol は信頼し、Fake で代替する
- Protocol クラス自体はテストしない（実装クラスや Fake のテストで間接検証する）

### テスト優先順位

テストケースはハッピーパス（正常系）を最優先で作成する。

- エッジケースは挙動が変わる入力のみテストする
- 過剰なエラーケーステストは作らない

### テストの独立性

各テストメソッドは他のテストメソッドに依存しない。
テストの実行順序が変わっても結果が変わらないようにする。
共有状態（クラス変数・グローバル変数）を使わない。

## Fake パターン

### 設計思想

Fake は Protocol に適合する具象クラスである。
Protocol の定義に従ってメソッドシグネチャを実装し、テスト目的に特化した振る舞いを持たせる。

### Fake の適用判断基準

副作用のないビジネスロジックには Fake を使わず、実クラスを直接テストする。
Fake 化は副作用境界のみに限定する。

| カテゴリ | Fake |
|----------|------|
| ファイル I/O、ネットワーク | 必須 |
| プロセス実行（subprocess） | 必須 |
| 非決定的処理（時刻取得、乱数生成） | 必須 |
| データ変換、計算 | 不要（実クラスを使用） |

### Fake の配置ルール

| 配置先 | 対象 |
|--------|------|
| `tests/fake/` | 複数のパッケージのテストで共有する Fake クラス |
| `tests/unit/test_<package>/helper.py` | 特定パッケージのテストのみで使う値オブジェクトファクトリ関数 |
| `tests/unit/test_<package>/fake.py` | 特定パッケージのテストのみで使う Fake クラス |

`tests/fake/` は Fake クラスのみで構成する。

| ファイル | 内容 |
|--------|------|
| `fake/xxx.py` | Protocol に適合する Fake クラス（`FakeXxx` 等） |

値オブジェクト生成ファクトリ関数（`make_xxx` 等）は、利用するテストパッケージの `helper.py` に定義する。
ファクトリ関数はアンダースコアを付けず公開関数として定義し、各テストファイルから明示的に import する。

### Fake の実装パターン

Protocol のメソッドシグネチャを遵守しつつ、コンストラクタで戻り値をセットする。

```python
class InMemoryFsReader:
    """TextFileSystemReaderProtocol の InMemory 実装"""

    def __init__(self, contents: FileContents) -> None:
        self._contents = contents

    def read(self, file_path: Path) -> str:
        return self._contents[str(file_path)]
```

## テストの命名規則

### テストクラス名

テスト対象クラス名に `Test` プレフィックスを付ける。

```
FooOrchestrator  →  TestFooOrchestrator
```

テストクラスには、テスト対象クラスを示す1行 docstring を付ける。

```python
class TestFooOrchestrator:
    """FooOrchestrator クラスのテスト"""
```

テストメソッドに docstring は付けない（テストメソッド名で自明なため）。

### テストメソッド名

`test_<対象メソッド>_<系統>_<期待する振る舞い>` の形式で日本語を用いて命名する。

| 要素 | 内容 | 例 |
|------|------|-----|
| `<対象メソッド>` | テスト対象のメソッド名（英語） | `orchestrate`、`provide`、`find_by_id` |
| `<系統>` | 正常系 / 異常系 / エッジケース | `正常系`、`異常系`、`エッジケース` |
| `<期待する振る舞い>` | テストが確認する内容（日本語） | `XxxReportを返すこと`、`エラーが発生すること` |

```python
def test_orchestrate_正常系_XxxReportを返すこと(self): ...
def test_provide_正常系_XxxOrchestratorインスタンスを返すこと(self): ...
def test_find_by_id_異常系_対象が存在しない場合エラーが発生すること(self): ...
```

## テストの構造

### パッケージ構成

テストパッケージの `__init__.py` は空ファイルにする。

### フィクスチャの使い方

pytest の `tmp_path` フィクスチャを積極的に使い、ファイルシステムを使うテストで一時ディレクトリを確保する。
インテグレーションテストでは `tmp_path` をベースに専用フィクスチャを定義する。

```python
@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """インテグレーションテスト用ワークスペース"""
    test_dir = tmp_path / "integration_test"
    test_dir.mkdir()
    return test_dir
```

## ユニットテスト

### 異常系テストの設計基準

異常系テストは `raise` 句またはバリデーションのあるクラスのみ作成する。

| レイヤー | 異常系テストの粒度 |
|---------|-------------------|
| 基盤層 | raise するエラーパターンごと |
| BL層 | 自クラスの `raise` / バリデーションがある場合のみ |
| CLI層 | 終了コード・出力のみ |

例外テストでは例外の型のみ検証し、エラーメッセージの文言はテストしない。

### プロダクションコードとの1対1マッピング

テストファイルはプロダクションコードのファイルと1対1で対応させる。

```
src/xxx/feature/orchestrator.py  →  tests/unit/test_feature/test_orchestrator.py
src/xxx/feature/parser.py        →  tests/unit/test_feature/test_parser.py
src/xxx/feature/formatter.py     →  tests/unit/test_feature/test_formatter.py
```

### Orchestrator テスト

Orchestrator のテストでは、コンストラクタに Fake を注入して振る舞いを検証する。

```python
class TestXxxOrchestrator:
    def test_orchestrate_正常系_変換結果をXxxResultとして返すこと(self, tmp_path: Path):
        # Arrange
        reader = InMemoryFsReader(...)
        orchestrator = XxxOrchestrator(parser=XxxParser(reader=reader), ...)
        context = XxxContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert result.exit_code == 0
```

### Provider テスト（Composition Root の検証）

Provider テストは、`provide()` が返すオブジェクトの型を検証する。
Orchestrator の各フィールドに正しい具象クラスが注入されていることを確認する。

```python
class TestXxxOrchestratorProvider:
    def test_provide_正常系_XxxOrchestratorインスタンスを返すこと(self):
        # Act
        result = XxxOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, XxxOrchestrator)
        assert isinstance(result.parser, XxxParser)
```

Provider テストでは Fake を使わず、実際の依存関係グラフが正しく構築されることを検証する。

## インテグレーションテスト

### subprocess 方式

外部通信を伴わないインテグレーションテストは `subprocess.run` で CLI を子プロセスとして起動し、標準出力・標準エラー出力・終了コードを検証する。

```python
def test_process_正常系_エラーなしでexit_code_0(self, tmp_dir: Path):
    # Arrange
    src_dir = tmp_dir / "src"
    src_dir.mkdir()
    py_file = src_dir / "main.py"
    py_file.write_text("x = 1\n")

    # Act
    cmd = [sys.executable, "-m", "xxx.cli", "process", str(src_dir)]
    result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

    # Assert
    assert result.returncode == 0
    assert "status: ok" in result.stdout
```

subprocess 方式を採用する理由は次のとおりである。

- CLI の引数解析・環境変数読み込み・終了コードまで含めたエンドツーエンド検証ができる
- プロセス境界を越えることで、実際の動作環境に近い検証ができる
- `pyproject.toml` の `patch = ["subprocess"]` 設定により、子プロセスのカバレッジも計測できる

### runner.invoke 方式

外部 API やネットワーク通信を伴うコマンドでは、`runner.invoke(app, ...)` でインプロセス実行し、`pytest.MonkeyPatch` で外部通信のみ差し替える。

```python
def test_fetch_正常系_API結果を出力(self, monkeypatch: pytest.MonkeyPatch):
    # Arrange
    monkeypatch.setattr("xxx.external.api.fetch", lambda: {"status": "ok"})
    runner = CliRunner()

    # Act
    result = runner.invoke(app, ["fetch"])

    # Assert
    assert result.exit_code == 0
```

runner.invoke 方式を採用する理由は次のとおりである。

- 外部 API を毎回実行すると相手サーバーへの負荷になる（DoS と変わらない）
- インプロセス実行のため `pytest.MonkeyPatch` で外部依存を差し替えられる

### 方式の選択基準

| 条件 | 方式 |
|------|------|
| 外部 API/ネットワーク通信がない | subprocess 方式 |
| 外部 API/ネットワーク通信がある | runner.invoke 方式 |

### テストケースの選定基準

インテグレーションテストはハッピーパス（正常系の代表ケース）を中心に選ぶ。
境界値・エラー系・詳細な条件分岐はユニットテストで網羅する。

### ユニットテストとの棲み分け

| 観点 | ユニットテスト | インテグレーションテスト |
|------|------------|---------|
| テスト数 | 多い（境界値・エラー系・詳細ケース） | 少ない（ハッピーパス中心） |
| 実行速度 | 高速 | 低速（プロセス起動コストあり） |
| 追加基準 | 新しいクラス・メソッドを追加したとき | ユニットテストで代替できないエンドツーエンドの検証が必要なとき |

## E2Eテスト

### 目的と位置づけ

E2Eテストは `docs/rules/` に定義されたルール仕様と実装の一致を検証する。
ユニットテスト・インテグレーションテストとの比較は次のとおりである。

| 観点 | ユニットテスト | インテグレーションテスト | E2Eテスト |
|------|------------|---------|---------|
| 検証対象 | クラス・関数の振る舞い | コンポーネント間の統合 | ルール仕様と実装の一致 |
| テストデータ | Fake / `tmp_path` で動的生成 | `tmp_path` で動的生成 | 静的 Fixture ファイル |
| カバレッジ計測 | 対象 | 対象 | 対象外 |
| テスト数 | 多い | 少ない | ルールごとに数件 |

### ディレクトリ配置

E2Eテストは `e2e-tests/` をリポジトリルート直下に置く。`tests/` 配下ではなく独立させる理由は次のとおりである。

- 違反 Fixture は意図的にルール違反を含む Python ファイルである。`tests/` 配下に置くと Paladin 実行時に警告対象となる
- `pyproject.toml` の `testpaths = ["tests"]` を変更せず、`make test-e2e` で明示的に制御できる
- pyright の `include = ["src", "tests"]` にも影響しない（Fixture の型エラーを回避できる）
- `pyproject.toml` の ruff exclude に `"e2e-tests/**/fixtures"` を追加し、Fixture のみリント対象外にしつつテストコード自体はリント対象に保てる

### ディレクトリ構造

ルールごとのサブディレクトリを作成し、各ルールの Fixture とテストを自己完結させる。

```
e2e-tests/
├── conftest.py
├── max-order-amount/
│   ├── fixtures/
│   │   ├── violation/
│   │   │   └── over_limit_order.py
│   │   └── compliant/
│   │       └── normal_order.py
│   └── test_e2e_max_order_amount.py
├── require-billing-address/
│   ├── fixtures/
│   │   ├── violation/
│   │   │   └── src/example/...
│   │   └── compliant/
│   │       └── src/example/...
│   └── test_e2e_require_billing_address.py
└── <rule-id>/
    ├── fixtures/
    │   ├── violation/
    │   │   └── ...
    │   └── compliant/
    │       └── ...
    └── test_e2e_<rule_id>.py
```

- `violation/` と `compliant/` を物理的に分離し、Fixture の役割を明確にする
- 複数ファイルルールは `src/` 配下にパッケージ構造を再現する
- 各ルールの Fixture が他ルールに干渉しない

### Fixture 設計

Fixture は次の3原則に従って作成する。

- 仕様準拠: `docs/rules/<rule-id>.md` の検出パターンをベースにする
- 分離性: 違反 Fixture は対象ルールの違反のみを含む（他ルールの違反を回避するため `__all__` 追加等を行う）
- 最小性: 検出・非検出を確認できる最小限のコードにする

単一ファイルルールの Fixture は1ファイルで完結させる。
複数ファイルルール（`require-billing-address` 等）は `src/` 配下にパッケージ構造を再現する。

### Fixture 分離ポリシー

Fixture 設計の **分離性** をディレクトリ構成レベルで実現するためのポリシーである。
各テストメソッドは、独立したフィクスチャディレクトリを指定する。

- テストシナリオごとに専用のフィクスチャディレクトリを持つ
- 既存の `violation/` や `compliant/` に異なるシナリオのファイルを混在させない
- 混在させるとフィクスチャの意図が不明確になり、変更時の影響範囲が拡大する

基本パターンは `violation/` と `compliant/` の2ディレクトリ構成である。
同じカテゴリ（violation または compliant）で複数のシナリオが必要な場合は、`{カテゴリ}_{シナリオ名}` 形式の追加ディレクトリを作成する。

```
e2e-tests/no-duplicate-line-item/
├── fixtures/
│   ├── violation/              # 基本の違反シナリオ
│   ├── compliant/              # 基本の準拠シナリオ
│   └── compliant_bulk_order/   # 一括注文固有の準拠シナリオ
└── test_e2e_no_duplicate_line_item.py
```

追加ディレクトリを作成する判断基準は次のとおりである。

- 既存フィクスチャとは異なるディレクトリ構造（`tests/` の有無など）が必要な場合
- 既存フィクスチャにファイルを追加すると、別のテストメソッドの前提条件が崩れる場合
- テストが検証する観点が異なり、1つのフィクスチャに混在させると意図が不明確になる場合

### テストの実行方式

E2Eテストは `subprocess.run` で `xxx process <fixture-path>` を子プロセスとして起動し、標準出力と終了コードを検証する。

| テストの種類 | 検証項目 |
|------------|---------|
| 違反検出テスト | `returncode == 1` かつ stdout にルール ID が含まれる |
| 準拠確認テスト | `returncode == 0` |

`conftest.py` に共通の subprocess 実行ヘルパーを定義し、各テストファイルから呼び出す。

### テストの命名規則

| 要素 | 規則 | 例 |
|------|------|-----|
| ディレクトリ名 | ルール ID そのまま | `max-order-amount/` |
| テストファイル名 | `test_e2e_<rule_id>.py` | `test_e2e_max_order_amount.py` |
| テストクラス名 | `TestE2E<RuleName>` | `TestE2EMaxOrderAmount` |
| 違反検出メソッド | `test_check_違反検出_<振る舞い>` | `test_check_違反検出_上限超過の注文が違反として報告されること` |
| 準拠確認メソッド | `test_check_準拠確認_<振る舞い>` | `test_check_準拠確認_上限内の注文で違反が報告されないこと` |

## ガードレール

### 禁止事項

| ルール | 理由 |
|-------|------|
| `unittest.mock` / `pytest-mock` の `MagicMock` / `patch` を使わない | Protocol + Fake で型安全に分離できる。Mock は型チェックを回避する |
| `@pytest.mark.parametrize` は入力バリエーションの列挙に限定する | テストロジックが共通で入力のみ異なるケースでは `pytest.param(id=...)` で識別する。アサート分岐を含む複雑な parametrize は避ける |
| テストクラスをネストしない | フラットな構造で十分。ネストは可読性を下げる |
| テスト間で状態を共有しない（クラス変数・グローバル変数） | テストの実行順依存を防ぐ |
| `conftest.py` にビジネスロジックを持ち込まない | `conftest.py` はフィクスチャの定義のみ |
| プロダクションコードにテスト専用パラメータを追加しない | テスト分離は Fake や DI で解決する |
| `assert` をヘルパー関数でラップしない | テスト失敗時の原因特定が困難になる |
| 型チェッカーで保証される振る舞いをテストしない | `frozen=True` の不変性や型不一致の `TypeError` は pyright で検出済み |
| 実装詳細（private 属性、メソッド呼び出し引数・回数）をテストしない | リファクタリング耐性が低下する。公開メソッドの戻り値と副作用のみ検証する |
