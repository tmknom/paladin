# require-all-export

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | require-all-export |
| 対象 | 単一ファイル |

## 概要

`__init__.py` に `__all__` の定義を要求するルールです。`__init__.py` ファイルに `__all__` リストが定義されていない場合に違反を検出します。

## 背景と意図

Python パッケージの `__init__.py` は、外部に公開するシンボルの窓口です。`__all__` を定義することで、パッケージの公開インタフェースが明示的になり、意図しないシンボルの漏れ出しを防げます。

`__all__` が定義されていない場合、`from package import *` によってプライベートな実装詳細が外部に露出するリスクがあります。また、IDEや静的解析ツールが公開APIを正確に把握できず、パッケージの利用者が意図しないシンボルに依存してしまう可能性があります。このルールは、パッケージ設計における明示的な公開インタフェースの定義を強制し、カプセル化を維持するために必要です。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `__init__.py` に `__all__` が定義されていない |
| reason | `__all__` が未定義の場合、パッケージの公開インタフェースが不明確になり、意図しないシンボルが外部に露出するリスクがある |
| suggestion | `__all__ = [{symbols}]` のように公開シンボルを定義してください（公開シンボルが検出できない場合は「`__all__` リストを定義し、公開するシンボルを明示的に列挙してください」にフォールバック） |

## 検出パターン

### 違反コード

`__all__` が定義されていない `__init__.py` は違反です。

```python
from myapp.services.data.error import DataError
from myapp.services.data.loader import DataLoader

# __all__ が定義されていない
```

### 準拠コード

`__all__` が定義され、公開シンボルのみを列挙しているケースは準拠です。

```python
from myapp.services.data.error import DataError
from myapp.services.data.loader import DataLoader
from myapp.services.data.protocol import DataLoaderProtocol, DataWriterProtocol
from myapp.services.data.types import LoadResult
from myapp.services.data.writer import DataWriter

__all__ = [
    "DataError",
    "DataLoader",
    "DataLoaderProtocol",
    "DataWriter",
    "DataWriterProtocol",
    "LoadResult",
]
```

## 検出の補足

このルールは単一ファイル内で完結します。対象ファイルが `__init__.py` であるかどうかの判定と、`__all__` の存在確認のみを行います。

空の `__init__.py`（名前空間パッケージのマーカーファイルとして使われるもの）はスコープ外とします。ファイルの内容が空、またはコメントのみの場合は違反として検出しません。

`__all__` の内容と import 文の整合性チェック（定義されているが列挙が不足している、import していないシンボルが含まれているなど）は、このルールのスコープ外です。将来的に別ルールで扱う可能性があります。

## 既存ツールとの関係

Ruff の `PLC0414` は再エクスポートの明示化（`import X as X`）に関するルールであり、`__all__` の定義有無を検査するものではありません。Ruff には `__all__` 関連のチェック（`F401` など）が存在しますが、`__init__.py` における `__all__` の定義を必須とするルールは提供されていません。

Paladin でこのルールを扱う理由は、パッケージの公開インタフェース設計という観点からの検査であり、既存ツールの文法的・スタイル的チェックとは目的が異なります。
