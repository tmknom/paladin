# Pythonテスト設計

本プロジェクトのPythonテストコードにおける設計原則・構造・パターンを示す。
開発コマンドや TDD の進め方は [Python開発ワークフロー](workflow.md) に、Protocol の設計思想は [Pythonアーキテクチャ設計](architecture.md) に委ねる。

## テストの種類と配置

本プロジェクトはユニットテストと統合テストの2種類を使い分ける。

| 種類 | 配置先 | 実行コマンド | スコープ | 外部依存 |
|------|--------|------------|--------|--------|
| ユニットテスト | `tests/unit/` | `make test-unit` | 単一クラス・関数の振る舞い | Fake で完全に分離する |
| 統合テスト | `tests/integration/` | `make test-integration` | CLI から結果出力までのエンドツーエンド | 外部ネットワークのみ分離する |

`tests/unit/` の内部構造はプロダクションコードのパッケージ構成をミラーリングする。
対応するプロダクションパッケージに `test_` プレフィックスを付けたディレクトリ名を使う。

```
src/paladin/check/          →  tests/unit/test_check/
src/paladin/config/         →  tests/unit/test_config/
src/paladin/foundation/fs/  →  tests/unit/test_foundation/test_fs/
```

## テスト設計の原則

### Fake によるテスト分離

ユニットテストでは Mock を使わず、Protocol に適合する具象クラス（Fake）で外部依存を分離する。
Fake の設計と実装パターンの詳細は [Fake パターン](#fake-パターン) を参照。

### Protocol との連携

Fake は [Pythonアーキテクチャ設計](architecture.md) で定義する Protocol の Structural Subtyping を利用する。
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

共有 Fake の例: `InMemoryFsReader`（`tests/unit/fakes/fs.py`）、`FakeRule`（`tests/unit/fakes/rule.py`）

パッケージ固有 Fake の例: `InMemoryFsWriter`（`tests/unit/test_transform/fakes.py`）

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

- コンストラクタ引数でテストシナリオを設定する（戻り値・エラー）
- メソッド呼び出しを記録するリストフィールドを持つ（`read_paths`）
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

### ヘルパー関数の使い方

テスト間で共通する Arrange のセットアップを `_make_` プレフィックスのヘルパー関数に切り出す。
クラスメソッドとして定義し、テストメソッドから呼び出す。

```python
def _make_orchestrator(self, reader: InMemoryFsReader) -> CheckOrchestrator:
    return CheckOrchestrator(
        collector=FileCollector(),
        parser=AstParser(reader=reader),
        ...
    )
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

統合テストは `subprocess.run` で CLI を子プロセスとして起動し、標準出力・終了コードを検証する。

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

## ガードレール

### 禁止事項

| ルール | 理由 |
|-------|------|
| `unittest.mock` / `pytest-mock` の `MagicMock` / `patch` を使わない | Protocol + Fake で型安全に分離できる。Mock は型チェックを回避する |
| `@pytest.mark.parametrize` を使わない | 各テストメソッドが独立した意図を持ち、命名で識別できることを優先する |
| テストクラスをネストしない | フラットな構造で十分。ネストは可読性を下げる |
| テスト間で状態を共有しない（クラス変数・グローバル変数） | テストの実行順依存を防ぐ |
| `conftest.py` にビジネスロジックを持ち込まない | `conftest.py` はフィクスチャの定義のみ |
