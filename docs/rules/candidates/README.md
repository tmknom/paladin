# 設計ルール候補

## 概要

本ディレクトリでは、Paladinでのサポートを検討している、設計ルールの候補一覧を提供します。
実装済みのルールは「[設計ルール](../README.md)」を参照してください。

## 設計ルールの候補一覧

| ルール名 | 概要 |
|----------|------|
| [no-cross-package-reexport](no-cross-package-reexport.md) | 別パッケージのシンボルを自パッケージの `__all__` で再エクスポートすることを禁止する |
| [no-unused-export](no-unused-export.md) | `__init__.py` の `__all__` に定義したシンボルが別パッケージから利用されていないことを禁止する |
| [no-mock-usage](no-mock-usage.md) | `unittest.mock.Mock` / `MagicMock` の使用を禁止する |
