# no-relative-import

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-relative-import |
| 対象 | 単一ファイル |

## 概要

相対インポート（`from . import Foo` や `from ..module import Bar` など）を検出するルールです。すべてのインポートに絶対インポートを使用することを強制します。

## 背景と意図

相対インポートはモジュール間の依存関係を暗黙的にします。どのパッケージに依存しているかをファイル単体で把握できず、コードの読み手がディレクトリ構造を常に意識しなければなりません。

また、モジュールを別のパッケージへ移動した場合、相対インポートはすべて書き直しが必要になります。絶対インポートであれば、移動先のファイル内のインポートは変更不要であり、参照元のみ修正すれば済みます。

絶対インポートを強制することで、依存関係を明示的に保ち、リファクタリング時のコストを低減します。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | 相対インポートが使用されている（`from {level_dots}{module} import ...`） |
| reason | 相対インポートは依存関係を不透明にし、モジュール移動時にインポートパスの修正が必要になる |
| suggestion | `from {level_dots}{module} import {names}` をプロジェクトルートからの絶対インポートに書き換えてください |

## 検出パターン

### 違反コード

```python
from . import DataLoader
from .protocol import DataLoaderProtocol
from ..error import ApplicationError
from ...config import Config
from ....services.data import DataLoader
```

### 準拠コード

```python
from myapp.services.data import DataLoader
from myapp.services.data.protocol import DataLoaderProtocol
from myapp.services.error import ApplicationError
from myapp.config import Config

from pathlib import Path
import logging
```

## 検出の補足

AST の `ImportFrom` ノードが持つ `level` 属性が 1 以上であれば相対インポートと判定します。`level` はドットの数に対応し、`.` で 1、`..` で 2、以降同様に増加します。ドット数にかかわらず、`level >= 1` のすべてのケースが違反です。

`import module` 形式（`Import` ノード）は相対インポートを文法上サポートしないため、検出対象外です。`from` 形式（`ImportFrom` ノード）のみが対象となります。

標準ライブラリやサードパーティライブラリへの絶対インポートは違反になりません。

## 既存ツールとの関係

Ruff のルール `TID252`（絶対インポート必須）が同等の検出を行います。`TID252` を有効化している場合、このルールと重複します。

Paladin でこのルールを提供する理由は、Ruff を導入していないプロジェクトでも設計ルールとして一貫して適用できるようにするためです。また、Paladin の診断メッセージ形式（message / reason / suggestion）で出力することで、他の Paladin ルールと統一されたフィードバックを得られます。
