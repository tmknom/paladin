# no-non-init-all

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-non-init-all |
| 対象 | 単一ファイル |

## 概要

`__init__.py` 以外のモジュールに `__all__` を定義することを禁止するルールです。`__init__.py` 以外のファイルに `__all__` が定義されている場合に違反を検出します。

## 背景と意図

`__all__` はパッケージの公開インタフェースを制御するための仕組みです。その役割は `__init__.py` に限定すべきであり、個別モジュールに定義すると以下の問題が生じます。

- `__all__` がパッケージの公開APIを表すのか、モジュール内の補助的な情報なのか判断できず、読み手が混乱する
- `__init__.py` の `__all__` がパッケージの唯一の公開API定義であるという設計原則が崩れる
- モジュールレベルの `__all__` は `from module import *` の挙動を制御するが、このパターン自体が避けるべき慣習であり、そのために `__all__` を書くことで誤った設計を促進する
- `__init__.py` の `__all__` と個別モジュールの `__all__` が矛盾する場合、実際の公開インタフェースが不明確になる

パッケージの公開APIは `__init__.py` の `__all__` のみで管理することで、公開インタフェースの定義が一か所に集まり、設計の意図が明確になります。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `__init__.py` 以外のファイルに `__all__` が定義されている |
| reason | `__all__` はパッケージの公開インタフェース定義であり、`__init__.py` のみで管理すべき |
| suggestion | `__all__` を削除してください。このモジュールのシンボルを公開する場合は、パッケージの `__init__.py` の `__all__` に追加してください |

## 検出パターン

### 違反コード

```python
# paladin/check/collector.py（__init__.py ではない）
from pathlib import Path

__all__ = ["FileCollector", "PathExcluder"]  # 違反: __init__.py 以外に __all__ が定義されている


class FileCollector:
    ...


class PathExcluder:
    ...
```

### 準拠コード

個別モジュールには `__all__` を定義せず、公開すべきシンボルはパッケージの `__init__.py` で管理します。

```python
# paladin/check/collector.py（__init__.py ではない）
from pathlib import Path


class FileCollector:
    ...


class PathExcluder:
    ...
```

```python
# paladin/check/__init__.py
from paladin.check.collector import FileCollector, PathExcluder

__all__ = [
    "FileCollector",
    "PathExcluder",
]
```

## 検出の補足

このルールは `__init__.py` 以外の `.py` ファイルを対象とします。`__init__.py` における `__all__` の定義はこのルールの対象外です（`require-all-export` ルールでその定義を要求しています）。

検出のロジックは以下のとおりです。

- 対象ファイルが `__init__.py` でないことを確認する
- ファイル内に `__all__` の代入文が存在する場合に違反として報告する

`__all__` の定義形式（リスト、タプルなど）や内容は検出に影響しません。代入が存在するだけで違反として扱います。

## 既存ツールとの関係

Ruff には `__init__.py` 以外のファイルにおける `__all__` の定義を禁止するルールはありません。`F401`（未使用インポート）や `PLC0414`（再エクスポートの明示化）は別の観点のルールであり、`__all__` の配置場所を検査するものではありません。

パッケージの公開インタフェース管理という設計上の意図を検出するルールとして、Paladin で独自に扱います。
