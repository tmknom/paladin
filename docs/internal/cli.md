# cli モジュール設計

## ファイルレイアウト

### プロダクションコード

```
src/paladin/
└── cli.py    # CLI エントリーポイント（単一ファイル）
```

### テストコード

CLI のテストはインテグレーションテストのみで、ユニットテストは存在しない。

```
tests/integration/
└── test_integration_cli.py    # CLI のインテグレーションテスト
```

## 処理フロー

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
            ├─ 実行オプションの優先度解決（CLI 引数 > AppConfig）
            ├─ Context を組み立てる
            ├─ OrchestratorProvider が Orchestrator を生成する
            ├─ Orchestrator がビジネスロジックを実行する
            └─ 実行結果を標準出力する
```

例外発生時は `main()` で捕捉し、`ErrorHandler` を実行後 `sys.exit(1)` で終了する。

## cli 固有の依存コンポーネント

cli モジュールでのみ実行するコンポーネント。

| コンポーネント | パッケージ | 用途 |
|---|---|---|
| `AppConfig` | `paladin.config` | アプリケーションの設定（ログレベルなど）を取得 |
| `EnvVarConfig` | `paladin.config` | 環境変数の読み込み |
| `ErrorHandler` | `paladin.foundation.error` | 例外ハンドリング |
| `LogConfigurator` | `paladin.foundation.log` | ログ設定の初期化 |

## 設計判断

### グローバルコールバックでの AppConfig 構築

`AppConfig` の構築を `main_callback` で行い、`typer.Context` に格納して各サブコマンドへ渡す。

**理由**: 設定構築を各サブコマンドで個別に行うと、`EnvVarConfig` の読み込みがサブコマンドの数だけ実行され、環境変数の読み込みタイミングが分散する。

**トレードオフ**: `main_callback` は `@app.callback()` に依存するため、ユニットテストよりインテグレーションテストで検証する方が適切になる。

### サブコマンド専用オプションの解決場所

サブコマンド専用の引数は、`AppConfig` を経由せず、サブコマンドの関数内で直接優先度を解決する。

**理由**: `AppConfig` は `main_callback` で呼ばれるが、その時点ではサブコマンド専用オプションの値がない。優先度解決をサブコマンド関数に置くことで、責務の所在が明確になる。

**トレードオフ**: 将来 `--tmp-dir` を複数コマンドで使う場合、各コマンド関数に同じ優先度解決ロジックが散在する。その時点で `AppConfig` への移行を検討する。

### main() での最上位例外ハンドリング

`main()` に try-except 句を置き、全例外を捕捉する。そして `ErrorHandler` を実行して `sys.exit(1)` で終了する。

**理由**: 例外ハンドリングをコードベース全体に分散させると、ビジネスロジックが追いづらくなる。アプリケーションでは基本的に例外をスローするだけとし、例外ハンドリングは一箇所で集約する。

**トレードオフ**: サブコマンドごとに異なるリカバリーロジックが必要になった場合は、各サブコマンド関数内での個別ハンドリングを追加する必要がある。

### インテグレーションテストのみによる検証

cli モジュールはユニットテストを持たず、インテグレーションテスト（`tests/integration/test_integration_cli.py`）のみで検証する。

**理由**: cli モジュールの責務はコンポーネントの「組み立て」と「委譲」であり、ビジネスロジックを持たない。各コンポーネントはそれぞれユニットテストで検証済みであるため、「コンポーネントが正しく組み合わさって動作するか」を確認すれば十分である。

**トレードオフ**: インテグレーションテストはファイルシステムや環境変数に依存するため、ユニットテストより実行コストが高い。

## ガードレール

- サブコマンド関数は `typer.Context` から `AppConfig` を取得すること。`EnvVarConfig` や `AppConfig` をサブコマンド関数内で再度呼び出してはならない
- 新しいグローバルオプションを追加する場合は `main_callback` に Typer Option を追加し、`AppConfig` の keyword-only 引数に渡す。サブコマンド関数に直接追加してはならない
- `sys.exit()` の呼び出しは `main()` 関数のみで行う

## 変更パターン別ガイド

| 変更内容 | 主な変更対象 | 備考 |
|---|---|---|
| 新しいサブコマンドを追加 | `@app.command()` 関数を追加 | `typer.Context` から `AppConfig` を取得するパターンを踏襲する |
| グローバルオプションを追加 | `main_callback` に Typer Option 追加、`AppConfig`（keyword-only 引数追加） | config パッケージの `AppConfig.build()` も合わせて更新する |
| サブコマンド専用オプションを追加 | サブコマンド関数に Typer Option 追加・優先度解決ロジック追加 | 優先度解決ロジックはサブコマンド関数内に置く（`AppConfig` に持たせない） |
| ビジネスロジックを変更 | cli モジュールの変更は不要（`<feature>` パッケージを変更） | - |
