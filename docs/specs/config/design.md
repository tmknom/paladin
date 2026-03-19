# config パッケージ基本設計

[config パッケージ要件定義](./requirements.md) に基づいた基本設計を説明します。

## アーキテクチャパターン

| パターン | 適用箇所 | 目的 |
|---|---|---|
| レイヤー分離 | `EnvVarConfig` / `PathConfig` / `AppConfig` | 読み込み・デフォルト値構築・合成の関心事を分離する |
| ファクトリーメソッド | `AppConfig.build()` / `PathConfig.from_base_dir()` | 呼び出し元がコンストラクタの詳細を知らずに設定を取得できる |
| 値オブジェクト | `AppConfig` / `PathConfig` | 生成後に変更できない不変オブジェクトとしてアプリケーション全体で安全に共有する |

## コンポーネント構成

### 主要コンポーネント

| コンポーネント | クラス名 | 役割 |
|---|---|---|
| 環境変数設定 | `EnvVarConfig` | 環境変数の読み込みとバリデーション |
| パス設定 | `PathConfig` | ベースディレクトリからのパス構築（内部コンポーネント） |
| アプリケーション設定 | `AppConfig` | 環境変数設定とパス設定の合成 |
| プロジェクト設定 | `ProjectConfig` / `PerFileIgnoreEntry` | `pyproject.toml` から読み込んだ設定値を保持する値オブジェクト |
| プロジェクト設定ローダー | `ProjectConfigLoader` | `pyproject.toml` の `[tool.paladin]` セクションをパースし `ProjectConfig` を生成する |
| 解析対象パス解決 | `TargetResolver` | CLI ターゲット引数と `ProjectConfig.include` を統合し、最終的な解析対象パスを返す |

### ファイルレイアウト

#### プロダクションコード

```bash
src/paladin/config/
├── __init__.py    # 公開 API の定義（AppConfig, EnvVarConfig, ProjectConfig, PerFileIgnoreEntry, ProjectConfigLoader, TargetResolver）
├── app.py         # AppConfig（設定の合成）
├── env_var.py     # EnvVarConfig（環境変数の読み込み）
├── path.py        # PathConfig（パス情報の構築、内部コンポーネント）
├── project.py     # ProjectConfig / PerFileIgnoreEntry / ProjectConfigLoader（プロジェクト設定）
└── resolver.py    # TargetResolver（解析対象パスの解決）
```

#### テストコード

```bash
tests/unit/test_config/
├── __init__.py
├── test_app.py        # AppConfig のテスト
├── test_env_var.py    # EnvVarConfig のテスト
├── test_path.py       # PathConfig のテスト
├── test_project.py    # ProjectConfig / PerFileIgnoreEntry / ProjectConfigLoader のテスト
└── test_resolver.py   # TargetResolver のテスト
```

## 処理フロー

### アプリケーション起動時の設定構築

1. `EnvVarConfig` を生成し、環境変数を読み込む（バリデーション含む）
2. `AppConfig` のファクトリーメソッドに `EnvVarConfig` を渡し、設定を合成する（CLIオプションも環境変数も指定されない項目は `PathConfig` が生成したデフォルト値で補完する）
3. 生成した `AppConfig` を CLI の Context へ格納し、各コマンドへ渡す
4. CLIオプションが指定されている場合、各コマンド関数または `main_callback` でその値を優先して適用する（優先順位: コマンドライン引数 > 環境変数 > デフォルト値）

### 解析コマンド実行時の設定構築

1. `ProjectConfigLoader` が `pyproject.toml` を読み込み、`ProjectConfig` を生成する
2. `TargetResolver` が CLI ターゲット引数と `ProjectConfig.include` を統合し、解析対象パスを決定する（どちらも未指定の場合はカレントディレクトリの `src` / `tests` をデフォルトとして使用する）
3. 解析対象パス・`ProjectConfig.exclude`・`ProjectConfig.per_file_ignores`・`ProjectConfig.rules` などを解析コアへ渡す

### 設定値の参照

各コマンドは `AppConfig` のフィールドを直接参照し、他パッケージの Context 構築（`TransformContext` など）に利用する。

## 固有の設計判断

### 3層構造による関心事の分離

**設計の意図**: 環境変数の読み込み（`EnvVarConfig`）、デフォルト値の構築（`PathConfig`）、それらの合成（`AppConfig`）を別クラスに分割した。

**なぜそう設計したか**: 単一クラスに全責務を持たせると、テスト時に環境変数とカレントディレクトリの両方を制御しなければならない。層を分けることで各コンポーネントを独立してテストできる。また、デフォルト値の決定ロジックを独立させることで、デフォルトパスの変更が `PathConfig` のみに局所化される。

**トレードオフ**: クラス数が増え、設定値を取得するまでの呼び出し経路が長くなる。一方で、それぞれのクラスの責務が単純になるためテストが容易になり、変更時の影響範囲が明確になる。

### 環境変数未設定とデフォルト値の責務分離

**設計の意図**: `EnvVarConfig` は `tmp_dir` が未設定の場合にデフォルト値を持たず、「設定されていない」ことを示す値を返す。デフォルト値の決定は `AppConfig` が担う。

**なぜそう設計したか**: `EnvVarConfig` がデフォルトパスを生成すると、パスの構築ロジックが環境変数クラスに混入する。責務を分離することで、環境変数クラスは「環境変数を読む」こと、合成クラスは「どの値を使うか決める」ことに専念できる。

**トレードオフ**: `AppConfig` の合成ロジックで未設定チェックが必要になる。ただしそのチェックは一箇所に集約されるため、変更コストは低い。

### `PathConfig` を公開 API に含めない

**設計の意図**: `PathConfig` は内部コンポーネントとして扱い、パッケージ外に公開しない。

**なぜそう設計したか**: 呼び出し元が必要とするのは「一時ディレクトリのパス」という値であり、その値がどのクラスで構築されたかは関心外である。内部実装を隠蔽することで、呼び出し元に影響なく `PathConfig` の設計を変更できる。

**トレードオフ**: `PathConfig` の構造変更は `AppConfig` の合成ロジックに波及するが、呼び出し元への影響は `AppConfig` のインターフェースが変わらない限り生じない。

### `pydantic-settings` によるバリデーション

**設計の意図**: `EnvVarConfig` は `pydantic-settings` を使い、環境変数の読み込みを宣言的に定義した。

**なぜそう設計したか**: 環境変数は文字列として取得されるが、アプリケーション内では型安全な値として扱いたい。`pydantic-settings` を使うことで型変換・バリデーション・デフォルト値の管理を1クラスに集約でき、未知の環境変数キーを拒否することで設定ミスを起動時に検出できる。

**トレードオフ**: `pydantic-settings` への依存が生まれる。未知のキーを拒否する設定により、将来的な設定追加時にはコードの変更が必須になる。

### `ProjectConfig` を値オブジェクトとして設計

**設計の意図**: `pyproject.toml` から読み込んだ設定全体（`per_file_ignores`・`rules`・`include`・`exclude`）を単一の不変値オブジェクト `ProjectConfig` に集約した。

**なぜそう設計したか**: 設定の各項目をバラバラに引き回すと、呼び出し側の引数が増え、設定の追加・削除のたびにシグネチャが変わる。1 つのオブジェクトにまとめることで、呼び出し元への影響を最小化し、設定の追加に対して拡張しやすい構造になる。

**トレードオフ**: `ProjectConfig` のフィールドが増えると、それを受け取るコンポーネントが不要なフィールドも保持することになる。ただし、設定の性質上フィールド数は限定的であり、現時点では問題とならない。

### `ProjectConfigLoader` にファイルシステム抽象を注入

**設計の意図**: `ProjectConfigLoader` はファイル読み込みを `TextFileSystemReaderProtocol` 経由で行い、具体的なファイルシステム実装に依存しない。

**なぜそう設計したか**: `pyproject.toml` への依存をハードコードすると、テスト時に実際のファイルシステムへのアクセスが必要になる。プロトコル（抽象インターフェース）を注入することで、テスト時に `InMemoryFsReader` などのフェイクへ差し替えられる。これにより、様々な TOML 内容を実ファイルなしでテストできる。

**トレードオフ**: 呼び出し元が `ProjectConfigLoader` に `TextFileSystemReaderProtocol` 実装を渡す必要がある。ただし、依存注入はこのプロジェクト全体で一貫して採用しているパターンであり、余分な複雑さとはならない。

### `TargetResolver` を config パッケージに配置

**設計の意図**: CLI ターゲット引数と設定ファイルの `include` を統合するロジックを `TargetResolver` として切り出し、check パッケージではなく config パッケージに置いた。

**なぜそう設計したか**: ターゲット解決は「CLI 入力と設定ファイルの統合」という性質であり、解析コアの責務ではなく設定管理の責務に属する。config パッケージに置くことで `CheckOrchestrator` が `CheckContext` 経由で解決済みパスだけを受け取れるようになり、解析コアの依存が整理される。

**トレードオフ**: `TargetResolver` の使用者が config パッケージをインポートする必要がある。ただし、CLI 層から呼び出されるユースケースが自然な配置であるため問題にならない。

### サブコマンド専用 CLIオプションの処理

**設計の意図**: `transform` サブコマンド専用の `--tmp-dir` オプションは、`AppConfig.build()` を経由せず、`transform` 関数内で直接優先度を解決する。

**なぜそう設計したか**: `--log-level` はグローバルな `main_callback` で `AppConfig` の構築と同時に解決されるが、`--tmp-dir` は `AppConfig` 構築後に呼ばれる `transform` 関数で処理される。`AppConfig.build()` にサブコマンド専用オプションを追加しても再構築の仕組みがなく、デッドコードになる。優先度解決ロジックを CLI 層のサブコマンド関数に置くことで、責務の所在が明確になる。

**トレードオフ**: 将来 `--tmp-dir` を複数コマンドで使う場合、各コマンド関数に同じ優先度解決ロジックが散在する。その時点で `AppConfig.build()` への移行を検討する。

## 制約と注意点

### 生成タイミング

設定オブジェクトはアプリケーション起動時に 1 回だけ生成する。複数回生成すると環境変数の状態によって異なる値が返される可能性があるため、生成したインスタンスを使い回すこと。

### `PathConfig` の利用スコープ

`PathConfig` はパッケージ内部の実装詳細であり、外部パッケージから直接 import してはならない（`from paladin.config.path import PathConfig` は禁止）。呼び出し元は `AppConfig` 経由でのみ値を取得すること。

### カレントディレクトリへの依存

`AppConfig` は `EXAMPLE_TMP_DIR` 未設定時に実行時のカレントディレクトリを参照する。テスト時はカレントディレクトリを明示的に制御すること。

### 公開 API の制限

公開 API は `AppConfig`・`EnvVarConfig`・`ProjectConfig`・`PerFileIgnoreEntry`・`ProjectConfigLoader`・`TargetResolver` のみ。内部コンポーネント（`PathConfig`）は外部パッケージからの import を想定しない。

### 未知の環境変数キーの拒否

`EnvVarConfig` は `extra="forbid"` の設定により、`EXAMPLE_` プレフィックスで始まる未定義の環境変数を検出した場合、アプリケーション起動時に `ValidationError` を送出する。これは設定ミス（例: `EXAMPLE_LOG_LEVLE` のような誤字）を起動時に検出するための意図的な設計である。新しい環境変数を追加する際は、必ず `EnvVarConfig` に対応するフィールドを追加すること。

## 外部依存と拡張性

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| `pydantic-settings` ライブラリ | 環境変数の読み込み・型変換・バリデーション |
| Python `pathlib` 標準ライブラリ | パス情報の表現と操作 |
| Python `tomllib` 標準ライブラリ（3.11+） | `pyproject.toml` のパース |
| `paladin.foundation.fs` / `paladin.protocol.fs` | ファイル読み込みの抽象インターフェース |
| `paladin.foundation.error` | `TargetResolver` の解析対象未指定エラー通知 |

### 想定される拡張ポイント

- **新しい環境変数の追加**: `EnvVarConfig` にフィールドを追加し、必要に応じて `AppConfig` に対応するフィールドを追加する
- **新しいパス情報の追加**: `PathConfig` に新しいパス構築ロジックを追加し、`AppConfig` に反映する
- **設定ソースの追加**: `pydantic-settings` は `.env` ファイルや他のソースにも対応しており、`EnvVarConfig` の設定を拡張することで対応できる
- **CLIオプションの追加**: `AppConfig.build()` に keyword-only 引数を追加し、`cli.py` の `main_callback` に対応する Typer Option を追加する
- **プロジェクト設定の新しい項目追加**: `ProjectConfig` にフィールドを追加し、`ProjectConfigLoader` に対応するパースロジックを追加する
- **解析対象パス解決ロジックの変更**: `TargetResolver.resolve()` のみを変更すればよく、解析コアへの影響はない

### 拡張時の注意点

- `EnvVarConfig` に新しいフィールドを追加する場合、未知のキーを拒否する設定が有効なため、既存の動作への影響はない
- `AppConfig` のインターフェースを変更した場合、`AppConfig` を利用している呼び出し元の修正が必要になる

## 変更パターン別ガイド

よくある変更ケースと、対応するコンポーネントの道筋を示す。

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| 新しい環境変数を追加 | `EnvVarConfig`（フィールド追加）、必要に応じて `AppConfig` へも反映 | `extra="forbid"` のため、コード変更なしに新しいキーは拒否される |
| 新しい設定値を `AppConfig` に追加 | `AppConfig`（フィールド追加・合成ロジック追加） | `cli.py` の `main_callback` に渡す引数も合わせて確認する |
| ログレベルの許容値を変更 | `EnvVarConfig` の `LogLevel` 型（`Literal` の値を追加・削除） | - |
| デフォルトパスの構築ルールを変更 | `PathConfig` | `AppConfig` の合成ロジックへの波及がないか確認する |
| 公開 API を追加 | `__init__.py`（内部コンポーネントの公開は原則行わない） | - |
| CLIオプションで設定を追加 | `AppConfig.build()`（keyword-only 引数追加・合成ロジック追加）、`cli.py`（Typer Option 追加） | グローバルオプションは `main_callback` に、サブコマンド専用は各コマンド関数に追加する |
| サブコマンド専用 CLIオプションで設定を上書き | `cli.py`（サブコマンド関数に Typer Option 追加・優先度解決ロジック追加） | 優先度解決ロジックはサブコマンド関数内に集約する |
| `pyproject.toml` に新しい設定項目を追加 | `ProjectConfig`（フィールド追加）、`ProjectConfigLoader`（パースロジック追加） | 追加したフィールドを使用するコンポーネントへの伝達方法も合わせて設計する |
| 解析対象パスの解決ロジックを変更 | `TargetResolver` | 解析コアには影響しない |

## 影響範囲

config パッケージを変更した場合、以下の呼び出し元に影響が及ぶ。

| 呼び出し元 | ファイル | 影響する変更 |
|---|---|---|
| CLI エントリーポイント | `src/paladin/cli.py` | `EnvVarConfig`・`AppConfig` のインターフェース変更全般 |
| ログ設定 | `src/paladin/cli.py` | `AppConfig.log_level` の型変更・デフォルト値変更・許容値の削除（`LogConfigurator` へ `AppConfig` 経由で渡している） |
| transform コマンド | `src/paladin/cli.py` | `AppConfig.tmp_dir` のインターフェース変更 |
| check コマンド | `src/paladin/cli.py` | `ProjectConfig`・`TargetResolver` のインターフェース変更 |
| `CheckOrchestrator` | `src/paladin/check/orchestrator.py` | `ProjectConfig` の各フィールドに依存しており、フィールド変更で影響を受ける |

## 関連ドキュメント

- [config パッケージ要件定義](./requirements.md): config パッケージの機能要件や前提条件
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
