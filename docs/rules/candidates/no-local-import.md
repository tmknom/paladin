# no-local-import

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-local-import |
| 対象 | 単一ファイル |

## 概要

関数内・クラス内・メソッド内に記述された import 文（ローカルインポート、遅延インポート）を検出するルールです。import 文はファイルのトップレベルに配置されていなければなりません。

## 背景と意図

import 文をファイル冒頭のトップレベルに集約することには、2つの重要な意図があります。

1つ目は依存関係の明示化です。ファイルの先頭を見るだけでそのモジュールが何に依存しているかを把握できる状態にしておくことで、コードレビューや依存関係の分析が容易になります。import 文が関数やクラスの内部に散在すると、依存関係の全体像を把握するためにファイル全体を精読しなければなりません。

2つ目はパフォーマンスの予測可能性です。ローカルインポートは関数やメソッドが呼ばれるたびにインポート処理のコストが発生する可能性があります。Python はモジュールをキャッシュするため実質的なコストは小さい場合もありますが、トップレベルにまとめることでインポートのタイミングが明確になり、起動時に依存モジュールの不在を早期検出できます。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `{scope}` 内に import 文があります |
| reason | import 文はモジュールのトップレベルに配置することで依存関係を明示し、インポートのタイミングを予測可能にします |
| suggestion | ファイル冒頭のインポートセクションに移動してください |

`{scope}` には、違反が検出された関数名・クラス名・メソッド名が入ります（例: `関数 some_function`、`メソッド SomeClass.method`）。

## 検出パターン

### 違反コード

関数内での import：

```python
def some_function():
    import requests
    response = requests.get(...)
```

クラスのメソッド内での import：

```python
class SomeClass:
    def method(self):
        from myapp.services.api import APIClient
```

ネストした関数内での import：

```python
def outer():
    def inner():
        import os
```

### 準拠コード

モジュールのドキュメント文字列の直後、トップレベルに import を配置する：

```python
"""モジュールのdocstring"""

import logging
from pathlib import Path

import requests
from requests.exceptions import RequestException

from myapp.services.api.error import APIError

def some_function():
    response = requests.get(...)
```

`TYPE_CHECKING` ブロック内の import はトップレベルに配置されているため違反としない：

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.services.api import APIClient
```

## 検出の補足

AST 上でモジュールトップレベルに存在しない `Import` ノードおよび `ImportFrom` ノードを違反として検出します。単一ファイルの AST 解析で完結するため、クロスファイルの解析は不要です。

`if TYPE_CHECKING:` ブロック内の import は検出対象外です。このブロックはモジュールレベルに配置されており、循環インポートを回避しながら型アノテーションで参照するモジュールを宣言するための慣用句です。実行時には評価されないため、ローカルインポートとは性質が異なります。

検出対象となるスコープは以下のとおりです。

- 関数定義（`def`）
- 非同期関数定義（`async def`）
- クラス定義（`class`）

モジュールレベルの条件分岐（`if TYPE_CHECKING:` を除く `if` 文など）の内部は、トップレベルではないものの慣用的に許容されるケースもあるため、現時点では検出対象外とします。

## 既存ツールとの関係

Ruff の `PLC0415`（`import-outside-toplevel`）が同等のチェックを提供しています。Ruff を導入済みのプロジェクトでは `PLC0415` を有効化することで同様の検出が可能です。

Paladin でこのルールを扱う理由は、Ruff を使用していないプロジェクトや、Paladin の統一されたルールセットとして import 配置のポリシーを明示的に管理したいプロジェクトのためです。Ruff の `PLC0415` を有効化している場合は、このルールとの重複を避けるため Paladin 側を無効化することを検討してください。
