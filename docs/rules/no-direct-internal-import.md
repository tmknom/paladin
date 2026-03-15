# no-direct-internal-import

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-direct-internal-import |
| 対象 | 複数ファイル |

## 概要

他パッケージの内部モジュールへの直接参照を禁止するルールです。`from package.submodule.internal import Foo` のように、パッケージの `__init__.py` を経由せず内部モジュールを直接インポートしている場合に違反を検出します。

## 背景と意図

パッケージは `__init__.py` を通じて公開 API を定義します。内部モジュールを直接インポートすると、パッケージの内部実装に依存することになり、以下の問題が生じます。

- パッケージ内部の構造変更（モジュール分割・移動・リネーム）が外部コードに直接影響する
- パッケージ作者が意図していない非公開シンボルへアクセスできてしまう
- パッケージの公開 API と内部実装の境界が曖昧になり、保守性が低下する

`__init__.py` を経由したインポートに統一することで、パッケージの公開インターフェースのみに依存する疎結合な設計を維持できます。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `from {module_path} import {name}` は内部モジュールへの直接参照である |
| reason | `{package}` の内部実装に直接依存しており、パッケージの公開 API を経由していない |
| suggestion | `from {package} import {name}` のように、パッケージの `__init__.py` を経由するインポートに書き換える |

## 検出パターン

### 違反コード

```python
# パッケージの内部サブモジュールを直接参照している
from myapp.services.data.loader import DataLoader
from myapp.extract.model.base import ModelLoader
from myapp.services.data.protocol import DataLoaderProtocol
```

### 準拠コード

```python
# パッケージの __init__.py を経由してインポートしている
from myapp.services.data import DataLoader, DataLoaderProtocol

from myapp.extract.model import ModelLoader
from myapp.services.data import DataLoaderProtocol
```

## 検出の補足

このルールは複数ファイルを横断して解析する `MultiFileRule` として実装されています。

- `__init__.py` が解析対象に含まれる場合は `__all__` と再エクスポート（`from .xxx import Yyy`）を解析して精密検出する
- `__init__.py` が解析対象にない、または公開シンボルの定義がない場合は「3階層以上の絶対インポート」をヒューリスティックで検出する
- インポート先がサブパッケージ（`__init__.py` を持つ）の場合は検出対象外とする。例えば `from myapp.foundation.model import Foo` の `myapp.foundation.model` がサブパッケージであれば、そのパッケージの公開 API を経由したインポートとして扱う
- 相対インポートによる内部モジュール直接参照は `no-relative-import` で別途検出するため、このルールは絶対インポートのみを対象とする
- 同一パッケージ内での内部モジュール参照（自パッケージの内部実装を自身で参照する場合）は検出対象外とする

## 既存ツールとの関係

Ruff にはこのルールに直接対応するルールがありません。Ruff の `TID252`（banned imports）はインポート禁止リストを静的に指定するものであり、`__init__.py` の公開 API に基づく動的な判定は行いません。パッケージ境界の設計上の意図を検出するルールとして、Paladin で独自に扱います。
