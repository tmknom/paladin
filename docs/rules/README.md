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
| [no-cross-package-reexport](no-cross-package-reexport.md) | 別パッケージのシンボルを自パッケージの `__all__` で再エクスポートすることを禁止する |
| [no-deep-nesting](no-deep-nesting.md) | 単一メソッド/関数内で3段階以上のネストを禁止する |
| [no-direct-internal-import](no-direct-internal-import.md) | 他パッケージの内部モジュールへの直接参照を禁止する |
| [no-non-init-all](no-non-init-all.md) | `__init__.py` 以外のモジュールに `__all__` を定義することを禁止する |
| [no-mock-usage](no-mock-usage.md) | Mock/MagicMock のインポートを禁止する |
| [no-unused-export](no-unused-export.md) | `__init__.py` の `__all__` に定義したシンボルが別パッケージから利用されていないことを禁止する |
| [no-third-party-import](no-third-party-import.md) | 許可ディレクトリ以外でのサードパーティライブラリのインポートを禁止する |
| [no-cross-package-import](no-cross-package-import.md) | 許可ディレクトリ以外のパッケージからのクロスパッケージインポートを禁止する |
| [no-testing-test-code](no-testing-test-code.md) | `tests/` 配下のコードに対するテストの作成を禁止する |
| [max-method-length](max-method-length.md) | 単一メソッド/関数の行数が設定された上限を超えた場合に違反を検出する |
| [max-class-length](max-class-length.md) | 単一クラスの行数上限を超えた場合に違反を検出する |
| [max-file-length](max-file-length.md) | 単一ファイルの行数上限を超えた場合に違反を検出する |
| [require-docstring](require-docstring.md) | モジュールおよびクラスに docstring の存在を要求する |
