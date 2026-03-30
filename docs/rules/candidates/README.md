# 設計ルール候補

## 概要

本ディレクトリでは、Paladinでのサポートを検討している、設計ルールの候補一覧を提供します。
実装済みのルールは「[設計ルール](../README.md)」を参照してください。

## 設計ルールの候補一覧

| ルール名 | 概要 |
|------------|------|
| [require-empty-test-init](require-empty-test-init.md) | テストパッケージの `__init__.py` が空ファイルであることを要求する |
| [no-nested-test-class](no-nested-test-class.md) | テストクラス内へのクラスのネストを禁止する |
| [require-test-class-docstring](require-test-class-docstring.md) | テストクラスに docstring の存在を要求する |
| [no-test-method-docstring](no-test-method-docstring.md) | テストメソッドへの docstring の記述を禁止する |
| [require-aaa-comment](require-aaa-comment.md) | テストメソッドに AAA コメント（`# Arrange` / `# Act` / `# Assert`）の存在を要求する |
| [no-frozen-instance-test](no-frozen-instance-test.md) | `FrozenInstanceError` を検証するテストを禁止する |
| [no-error-message-test](no-error-message-test.md) | 例外メッセージの文言を検証するテストを禁止する |
| [no-private-attr-in-test](no-private-attr-in-test.md) | テストコード内でのプライベート属性への直接アクセスを禁止する |
| [unused-ignore](unused-ignore.md) | 対応する違反が存在しない Ignore コメントを検出する |
