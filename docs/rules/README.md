# 設計ルール

## 概要

本ディレクトリでは、Paladinでサポートしている設計ルールの一覧を提供します。
未実装のルールは「[設計ルール候補](candidates/README.md)」を参照してください。

## 設計ルール一覧

| ルール名 | 概要 |
|------------|------|
| [require-all-export](require-all-export.md) | `__init__.py` に `__all__` の定義を要求する |
| [no-relative-import](no-relative-import.md) | 相対インポートを禁止する |
| [require-qualified-third-party](require-qualified-third-party.md) | サードパーティライブラリの完全修飾名使用を要求する |
| [no-local-import](no-local-import.md) | ファイル冒頭以外の場所での import を禁止する |
| [no-direct-internal-import](no-direct-internal-import.md) | 他パッケージの内部モジュールへの直接参照を禁止する |
