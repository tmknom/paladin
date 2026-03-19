# 設計ルール候補

## 概要

本ディレクトリでは、Paladinでのサポートを検討している、設計ルールの候補一覧を提供します。
実装済みのルールは「[設計ルール](../README.md)」を参照してください。

## 設計ルールの候補一覧

| ルール名 | 概要 |
|------------|------|
| [no-testing-test-code](no-testing-test-code.md) | `tests/` 配下のコードに対するテストの作成を禁止する |
| [no-third-party-import](no-third-party-import.md) | 許可ディレクトリ以外でのサードパーティライブラリのインポートを禁止する |
| [no-deep-nesting](no-deep-nesting.md) | 単一メソッド/関数内で3段階以上のネストを禁止する |
| [max-file-length](max-file-length.md) | 単一ファイルの行数上限を超えた場合に違反を検出する |
