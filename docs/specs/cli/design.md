# cli モジュール基本設計

[cli モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## アーキテクチャパターン

cli モジュールはアプリケーションの唯一のエントリーポイントである。
Typer をベースにして、次の構造を持つ。

### callback → command の2段階フロー

全サブコマンド共通の前処理（設定値の構築・ログ初期化）を `@app.callback()` に、
サブコマンド固有の処理を `@app.command()` に分離する。
前処理をコールバックに集約することで、設定構築がサブコマンドの数だけ重複しない。

### Config → Context → Orchestrator の連鎖

各サブコマンドは「環境設定の取得 → Context の組み立て → Orchestrator への委譲」という一方向の連鎖で処理を進める。
CLI 引数・環境設定・ランタイム情報を Context に一元化することで、Orchestrator が CLI の詳細を知らなくてよくなる。

### 最上位での例外一括捕捉

`main()` が全例外を捕捉し、個々のサブコマンドは例外を捕捉しない。
捕捉をエントリーポイントに集約することで、エラーログの形式と終了コードを一元管理する。

## コンポーネント構成

### 主要コンポーネント

| 要素 | 種別 | 役割 |
|---|---|---|
| `app` | `typer.Typer` インスタンス | サブコマンドの登録と CLI アプリケーション本体 |
| `main_callback` | `@app.callback()` 関数 | グローバル前処理（AppConfig 構築・ログ初期化） |
| `transform` | `@app.command()` 関数 | transform サブコマンドの実行 |
| `main` | 通常関数 | 最上位エントリーポイント・例外ハンドリング |

### ファイルレイアウト

#### プロダクションコード

```bash
src/example/
└── cli.py    # CLI エントリーポイント（単一ファイル）
```

#### テストコード

CLI のテストはインテグレーションテストのみで、ユニットテストは存在しない。

```bash
tests/integration/
└── test_integration_cli.py    # CLI のインテグレーションテスト
```

### cli モジュール固有の依存コンポーネント

cli モジュールではアプリケーション全体で重要になる、いくつかのコンポーネントを実行する。
これらのコンポーネントは、cli モジュールでのみ実行する。

| コンポーネント | パッケージ | 用途 |
|---|---|---|
| `AppConfig` | `example.config` | アプリケーションの設定（ログレベルなど）を取得 |
| `EnvVarConfig` | `example.config` | 環境変数の読み込み |
| `ErrorHandler` | `example.foundation.error` | 例外ハンドリング |
| `LogConfigurator` | `example.foundation.log` | ログ設定の初期化 |

## 処理フロー

### 全体フロー

```
main()
  └─ app()  ← Typer が CLI 引数を解析
       ├─ main_callback()  ← @app.callback()（全サブコマンド共通）
       │    ├─ EnvVarConfig() で環境変数を読み込む
       │    ├─ AppConfig で設定を合成する
       │    ├─ typer.Context に AppConfig を格納する
       │    └─ LogConfigurator でロガーを初期化する
       │
       └─ <feature>()  ← @app.command()（サブコマンド）
            ├─ typer.Context から AppConfig を取得する
            ├─ 実行オプションの優先度解決（CLI引数 > AppConfig）
            ├─ Context を組み立てる
            ├─ OrchestratorProvider が Orchestrator を生成する
            ├─ Orchestrator がビジネスロジックを実行する
            └─ 実行結果を標準出力する
```

### 例外発生時のフロー

1. `main()` で例外を捕捉する
2. `ErrorHandler` を実行し、エラーログの出力などを行う
3. `sys.exit(1)` でプロセスを異常終了させる


## 固有の設計判断

### グローバルコールバックでの AppConfig 構築

**設計の意図**: `AppConfig` の構築を `main_callback` で行い、`typer.Context` に格納して各サブコマンドへ渡す。

**なぜそう設計したか**: 設定構築を各サブコマンドで個別に行うと、`EnvVarConfig` の読み込みがサブコマンドの数だけ実行され、環境変数の読み込みタイミングが分散する。

**トレードオフ**: `main_callback` は Typer の `@app.callback()` に依存するため、ユニットテストよりインテグレーションテストで検証する方が適切になる。

### サブコマンド専用オプションの解決場所

**設計の意図**: サブコマンド専用の引数は、`AppConfig` を経由せず、サブコマンドの関数内で直接優先度を解決する。

**なぜそう設計したか**: `AppConfig` は `main_callback` で呼ばれるが、その時点ではサブコマンド専用オプションの値がない。優先度解決をサブコマンド関数に置くことで、責務の所在が明確になる。

**トレードオフ**: 将来 `--tmp-dir` を複数コマンドで使う場合、各コマンド関数に同じ優先度解決ロジックが散在する。その時点で `AppConfig` への移行を検討する。

### main() での最上位例外ハンドリング

**設計の意図**: `main()` に try-except 句を置き、全例外を捕捉する。そして `ErrorHandler` を実行して `sys.exit(1)` で終了する。

**なぜそう設計したか**: 例外ハンドリングをコードベース全体に分散させると、ビジネスロジックが追いづらくなる。そこでアプリケーションでは基本的に、例外をスローするだけとし、例外ハンドリングは一箇所で集約する。

**トレードオフ**: サブコマンドごとに異なるリカバリーロジックが必要になった場合は、各サブコマンド関数内での個別ハンドリングを追加する必要がある。

### インテグレーションテストのみによる検証

**設計の意図**: cli モジュールはユニットテストを持たず、インテグレーションテスト（`tests/integration/test_integration_cli.py`）のみで検証する。

**なぜそう設計したか**: cli モジュールの責務はコンポーネントの「組み立て」と「委譲」であり、ビジネスロジックを持たない。各コンポーネントはそれぞれユニットテストで検証済みであるため、cli モジュールでは「コンポーネントが正しく組み合わさって動作するか」を確認すれば十分である。

**トレードオフ**: インテグレーションテストはファイルシステムや環境変数に依存するため、ユニットテストより実行コストが高い。ただし cli モジュールに移動すべきロジックがない限り、この方針を維持する。

## 制約と注意点

### typer.Context への AppConfig 格納

`main_callback` は `AppConfig` を `typer.Context` に格納する。サブコマンド関数は `typer.Context` から `AppConfig` を取得すること。`EnvVarConfig` や `AppConfig` をサブコマンド関数内で再度呼び出してはならない。

### グローバルオプションの追加先

新しいグローバルオプション（全サブコマンドに共通するオプション）を追加する場合は `main_callback` に Typer Option を追加し、`AppConfig` の keyword-only 引数に渡す。サブコマンド関数に直接追加してはならない。

### sys.exit は main() のみ

`sys.exit()` の呼び出しは `main()` 関数のみで行う。サブコマンド関数内から `sys.exit()` を呼び出すと、`main()` の例外ハンドリングを実行できなくなる。

## 外部依存と拡張性

### 外部システム依存

| 依存先 | 用途 |
|---|---|
| `typer` ライブラリ | CLI フレームワーク（サブコマンド登録・引数解析・Context 管理） |
| Python `sys` 標準ライブラリ | プロセス終了（`sys.exit`） |

### 想定される拡張ポイント

- **新しいサブコマンドの追加**: `@app.command()` 関数を追加し、対応する Context と Orchestrator を組み立てる
- **グローバルオプションの追加**: `main_callback` に Typer Option を追加し、`AppConfig.build()` の keyword-only 引数として渡す

### 拡張時の注意点

- 新しいサブコマンドを追加する際は、`AppConfig` を `typer.Context` から取得するパターンを踏襲し、`main_callback` 内での再構築は行わないこと

## 変更パターン別ガイド

よくある変更ケースと、対応するコンポーネントの道筋を示す。

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| 新しいサブコマンドを追加 | `@app.command()` 関数を追加 | `typer.Context` から `AppConfig` を取得するパターンを踏襲する |
| グローバルオプションを追加 | `main_callback` に Typer Option 追加、`AppConfig`（keyword-only 引数追加） | config パッケージの `AppConfig.build()` も合わせて更新する |
| サブコマンド専用オプションを追加 | サブコマンド関数に Typer Option 追加・優先度解決ロジック追加 | 優先度解決ロジックはサブコマンド関数内に置く（`AppConfig` に持たせない） |
| 設定の許容値を変更 | cli モジュールの変更は不要（config パッケージを変更） | - |
| ビジネスロジックを変更 | cli モジュールの変更は不要（<feature> パッケージを変更） | - |

## 影響範囲

cli モジュールはアプリケーションのエントリーポイントであり、他のパッケージから依存されない。そのため cli モジュールへの変更が他パッケージに波及することはない。

ただし cli モジュール自体は `config`・`foundation/error`・`foundation/log`・`transform` の各パッケージに依存しているため、それらのパッケージの公開インターフェースが変更された場合は cli モジュールの修正が必要になる。

## 関連ドキュメント

- [cli モジュール要件定義](./requirements.md): cli パッケージの機能要件や前提条件
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
- [config パッケージ基本設計](../config/design.md): config パッケージのアーキテクチャ設計やコンポーネント構成
- [foundation/error パッケージ基本設計](../foundation/error/design.md): foundation/error パッケージのアーキテクチャ設計やコンポーネント構成
- [foundation/log パッケージ基本設計](../foundation/log/design.md): foundation/log パッケージのアーキテクチャ設計やコンポーネント構成
