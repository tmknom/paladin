# foundation/error パッケージ設計

## ファイルレイアウト

### プロダクションコード

```
src/paladin/foundation/error/
├── __init__.py    # 公開 API の定義（ApplicationError, ErrorHandler）
├── error.py       # ApplicationError（アプリケーション例外の基底クラス）
└── handler.py     # ErrorHandler（エラーハンドリング）
```

### テストコード

```
tests/unit/test_foundation/test_error/
└── test_error_handler.py    # ErrorHandler のテスト
```

## 設計判断

### ErrorHandler がプロセス終了を行わない設計

`ErrorHandler` は `sys.exit` を呼ばず、ログ記録のみを行い呼び出し元に制御を返す。

**理由**: `sys.exit` をハンドラ内で呼ぶとユニットテスト実行中にプロセスが終了してしまう。また、エラー後の挙動をアプリケーション側で柔軟に決定できる。プロセス終了を伴うテストは `tests/integration/test_integration_cli.py` でのみ実施する。

**トレードオフ**: 呼び出し元が `ErrorHandler.handle()` 後にプロセス終了を忘れると、エラー状態のまま処理が継続するリスクがある。

### ユーザー向けメッセージと開発者向け詳細の分離

`ApplicationError` はコンストラクタで `message`（ユーザー向け）と `cause`（開発者向け）を分離して受け取る。

**理由**: ユーザーに提示する内容と技術的なデバッグ情報は目的が異なり、単一の文字列に混在させると、ユーザーへの表示時に技術情報が漏れるリスクや、ログから必要情報を抽出しづらくなる問題が生じる。

**トレードオフ**: `cause` を省略した場合はデフォルト値（`"unexpected error occurred"`）が使われるため、詳細情報が不足したログが生成される可能性がある。

### 例外型による 2 系統のログフォーマット

`ErrorHandler` は `ApplicationError` と汎用 `Exception` でログフォーマットを切り替える。`ApplicationError` では `message`/`cause`（文字列フィールド）を活用し、汎用 `Exception` では `__cause__`（Python 標準の例外チェーン属性）を使って根本原因を記録する。

> `ApplicationError.cause`（文字列フィールド）と `Exception.__cause__`（Python 標準の例外チェーン属性）は名前が類似しているが別の概念である。

**理由**: `ApplicationError` は `message`/`cause` の構造が保証されているため、その情報を最大限活用できる。汎用 `Exception` には保証がなく、Python の標準的な例外チェーンが唯一の原因情報となる。

**トレードオフ**: 2 系統のフォーマッターを維持する必要があり、変更時はどちらを変更すべきかを意識する必要がある。

## ガードレール

- `ErrorHandler` はグローバルなエラーハンドリングクラスであり、`cli.py` の `main()` のような main 関数近くで利用することを想定している。他の機能パッケージへの組み込みはスコープ外
- `ApplicationError` と汎用 `Exception` の 2 系統以外の区別を追加する予定はない
- `sys.exit` の呼び出しは呼び出し元（main 関数）で実装すること
- ログ設定（ハンドラ・フォーマッタ・ログレベル）はこのパッケージが担当しない。アプリケーション起動処理で設定すること
- 公開 API は `ApplicationError` と `ErrorHandler` のみ。`paladin.foundation.error` パッケージから import すること

## 影響範囲

### `ApplicationError`

インターフェイス（プロパティの追加・削除）を変更するとコードベース全体に影響が及ぶ。継承しているすべてのアプリケーション例外クラスおよびその利用箇所が修正対象になるため、変更時は全パッケージへの影響を確認すること。

### `ErrorHandler`

インターフェイス（`handle()` メソッドのシグネチャ）を変更した場合の影響は、呼び出し箇所（= main 関数近く、基本的に 1 箇所）に集約される。振る舞い（ログフォーマット・出力内容）を変更した場合はアプリケーション全体のエラー時の挙動に影響する。
