# Pythonテスト設計

本プロジェクトのPythonテストコードにおける設計原則・構造・パターンを示す。

## テストの種類と配置

本プロジェクトはユニットテストと統合テストの2種類を使い分ける。

| 種類 | 配置先 | 実行コマンド | スコープ | 外部依存 |
|------|--------|------------|--------|--------|
| ユニットテスト | `tests/unit/` | `make test-unit` | 単一クラス・関数の振る舞い | Fake で完全に分離する |
| 統合テスト | `tests/integration/` | `make test-integration` | CLI から結果出力までのエンドツーエンド | 外部ネットワークのみ分離する |
| E2Eテスト | `e2e-tests/` | `make test-e2e` | ルール仕様と実装の一致検証 | 静的 Fixture ファイルのみ使用する |

`tests/unit/` の内部構造はプロダクションコードのパッケージ構成をミラーリングする。
対応するプロダクションパッケージに `test_` プレフィックスを付けたディレクトリ名を使う。

```
src/paladin/check/          →  tests/unit/test_check/
src/paladin/config/         →  tests/unit/test_config/
src/paladin/foundation/fs/  →  tests/unit/test_foundation/test_fs/
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

### テストの独立性

各テストメソッドは他のテストメソッドに依存しない。
テストの実行順序が変わっても結果が変わらないようにする。
共有状態（クラス変数・グローバル変数）を使わない。

## Fake パターン

### 設計思想

Fake は Protocol に適合する具象クラスである。
Protocol の定義に従ってメソッドシグネチャを実装し、テスト目的に特化した振る舞いを持たせる。

### Fake の配置ルール

| 配置先 | 対象 |
|--------|------|
| `tests/unit/fakes/` | 複数のパッケージのテストで共有する Fake |
| `tests/unit/test_<package>/fakes.py` | 特定パッケージのテストのみで使う Fake |

### Fake の実装パターン

コンストラクタで戻り値を事前設定し、呼び出しを記録するパターンを使う。

```python
class InMemoryFsReader:
    """TextFileSystemReaderProtocol の InMemory 実装"""

    def __init__(
        self,
        content: str = "",
        contents: dict[str, str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.content = content
        self.contents = contents
        self.error = error
        self.read_paths: list[Path] = []  # 呼び出し記録

    def read(self, file_path: Path) -> str:
        self.read_paths.append(file_path)  # 記録
        if self.error is not None:
            raise self.error
        if self.contents is not None:
            return self.contents[str(file_path)]
        return self.content
```

- コンストラクタ引数でテストシナリオ（戻り値・エラー）を設定する
- メソッド呼び出しをリストフィールド（`read_paths`）に記録する
- エラーケースは `error` 引数で注入する

## テストの命名規則

### テストクラス名

テスト対象クラス名に `Test` プレフィックスを付ける。

```
CheckOrchestrator  →  TestCheckOrchestrator
InMemoryFsReader   →  TestInMemoryFsReader
```

### テストメソッド名

`test_<対象メソッド>_<系統>_<期待する振る舞い>` の形式で日本語を用いて命名する。

| 要素 | 内容 | 例 |
|------|------|-----|
| `<対象メソッド>` | テスト対象のメソッド名（英語） | `orchestrate`、`provide`、`read` |
| `<系統>` | 正常系 / 異常系 / エッジケース | `正常系`、`異常系`、`エッジケース` |
| `<期待する振る舞い>` | テストが確認する内容（日本語） | `CheckReportを返すこと`、`エラーが発生すること` |

```python
def test_orchestrate_正常系_CheckReportを返すこと(self): ...
def test_provide_正常系_CheckOrchestratorインスタンスを返すこと(self): ...
def test_read_異常系_ファイルが存在しない場合エラーが発生すること(self): ...
```

## テストの構造

### AAA パターンのコメント規約

`# Arrange`、`# Act`、`# Assert` のコメントを必ず付ける。
補足が必要な場合はコメントを追記する。

```python
def test_orchestrate_正常系_ignore_fileディレクティブで違反が除外されること(self, tmp_path: Path):
    # Arrange
    init_file = tmp_path / "__init__.py"
    init_file.write_text("# paladin: ignore-file\nfrom foo import bar\n")
    ...

    # Act
    result = orchestrator.orchestrate(context)

    # Assert
    assert isinstance(result, CheckReport)
    assert result.exit_code == 0
```

### フィクスチャの使い方

pytest の `tmp_path` フィクスチャを積極的に使い、ファイルシステムを使うテストで一時ディレクトリを確保する。
統合テストでは `tmp_path` をベースに専用フィクスチャを定義する。

```python
@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """統合テスト用ワークスペース"""
    test_dir = tmp_path / "integration_test"
    test_dir.mkdir()
    return test_dir
```

## ユニットテスト

### プロダクションコードとの1対1マッピング

テストファイルはプロダクションコードのファイルと1対1で対応させる。

```
src/paladin/check/orchestrator.py  →  tests/unit/test_check/test_orchestrator.py
src/paladin/check/parser.py        →  tests/unit/test_check/test_parser.py
src/paladin/check/formatter.py     →  tests/unit/test_check/test_formatter.py
```

### Orchestrator テスト

Orchestrator のテストでは、コンストラクタに Fake を注入して振る舞いを検証する。

```python
class TestCheckOrchestrator:
    def test_orchestrate_正常系_列挙とAST生成の結果をCheckReportとして返すこと(
        self, tmp_path: Path
    ):
        # Arrange
        reader = InMemoryFsReader(contents={...})
        rule_set = RuleSet(rules=(FakeRule(violations=()),))
        orchestrator = CheckOrchestrator(
            collector=FileCollector(),
            parser=AstParser(reader=reader),
            rule_set=rule_set,
            ...
        )
        context = CheckContext(targets=(tmp_path,))

        # Act
        result = orchestrator.orchestrate(context)

        # Assert
        assert isinstance(result, CheckReport)
        assert result.exit_code == 0
```

### Provider テスト（Composition Root の検証）

Provider テストは、`provide()` が返すオブジェクトの型を検証する。
Orchestrator の各フィールドに正しい具象クラスが注入されていることを確認する。

```python
class TestCheckOrchestratorProvider:
    def test_provide_正常系_CheckOrchestratorインスタンスを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result, CheckOrchestrator)

    def test_provide_正常系_AstParserが注入されたOrchestratorを返すこと(self):
        # Act
        result = CheckOrchestratorProvider().provide()

        # Assert
        assert isinstance(result.parser, AstParser)
```

Provider テストでは Fake を使わず、実際の依存関係グラフが正しく構築されることを検証する。

## 統合テスト

### subprocess 方式

統合テストは `subprocess.run` で CLI を子プロセスとして起動し、標準出力・標準エラー出力・終了コードを検証する。

```python
def test_transform_正常系_ファイル変換を実行(self, tmp_dir: Path):
    # Arrange
    input_file = tmp_dir / "input.txt"
    input_file.write_text("test line", encoding="utf-8")

    # Act
    cmd = [sys.executable, "-m", "paladin.cli", "transform", str(input_file)]
    result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

    # Assert
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "src_length" in data
```

subprocess 方式を採用する理由は次のとおりである。

- CLI の引数解析・環境変数読み込み・終了コードまで含めたエンドツーエンド検証ができる
- プロセス境界を越えることで、実際の動作環境に近い検証ができる
- `pyproject.toml` の `patch = ["subprocess"]` 設定により、子プロセスのカバレッジも計測できる

### テストケースの選定基準

統合テストはハッピーパス（正常系の代表ケース）を中心に選ぶ。
境界値・エラー系・詳細な条件分岐はユニットテストで網羅する。

### ユニットテストとの棲み分け

| 観点 | ユニットテスト | 統合テスト |
|------|------------|---------|
| テスト数 | 多い（境界値・エラー系・詳細ケース） | 少ない（ハッピーパス中心） |
| 実行速度 | 高速 | 低速（プロセス起動コストあり） |
| 追加基準 | 新しいクラス・メソッドを追加したとき | ユニットテストで代替できないエンドツーエンドの検証が必要なとき |

## E2Eテスト

### 目的と位置づけ

E2Eテストは `docs/rules/` に定義されたルール仕様と実装の一致を検証する。
ユニットテスト・統合テストとの比較は次のとおりである。

| 観点 | ユニットテスト | 統合テスト | E2Eテスト |
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
├── no-relative-import/
│   ├── fixtures/
│   │   ├── violation/
│   │   │   └── relative_import.py
│   │   └── compliant/
│   │       └── absolute_import.py
│   └── test_e2e_no_relative_import.py
├── no-direct-internal-import/
│   ├── fixtures/
│   │   ├── violation/
│   │   │   └── src/example/...
│   │   └── compliant/
│   │       └── src/example/...
│   └── test_e2e_no_direct_internal_import.py
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
複数ファイルルール（`no-direct-internal-import` 等）は `src/` 配下にパッケージ構造を再現する。

### テストの実行方式

E2Eテストは `subprocess.run` で `paladin check <fixture-path>` を子プロセスとして起動し、標準出力と終了コードを検証する。

| テストの種類 | 検証項目 |
|------------|---------|
| 違反検出テスト | `returncode == 1` かつ stdout にルール ID が含まれる |
| 準拠確認テスト | `returncode == 0` |

`conftest.py` に共通の subprocess 実行ヘルパーを定義し、各テストファイルから呼び出す。

### テストの命名規則

| 要素 | 規則 | 例 |
|------|------|-----|
| ディレクトリ名 | ルール ID そのまま | `no-relative-import/` |
| テストファイル名 | `test_e2e_<rule_id>.py` | `test_e2e_no_relative_import.py` |
| テストクラス名 | `TestE2E<RuleName>` | `TestE2ENoRelativeImport` |
| 違反検出メソッド | `test_check_違反検出_<振る舞い>` | `test_check_違反検出_相対インポートが違反として報告されること` |
| 準拠確認メソッド | `test_check_準拠確認_<振る舞い>` | `test_check_準拠確認_絶対インポートのみで違反が報告されないこと` |

## ガードレール

### 禁止事項

| ルール | 理由 |
|-------|------|
| `unittest.mock` / `pytest-mock` の `MagicMock` / `patch` を使わない | Protocol + Fake で型安全に分離できる。Mock は型チェックを回避する |
| `@pytest.mark.parametrize` を使わない | 各テストメソッドが独立した意図を持ち、命名で識別できることを優先する |
| テストクラスをネストしない | フラットな構造で十分。ネストは可読性を下げる |
| テスト間で状態を共有しない（クラス変数・グローバル変数） | テストの実行順依存を防ぐ |
| `conftest.py` にビジネスロジックを持ち込まない | `conftest.py` はフィクスチャの定義のみ |
