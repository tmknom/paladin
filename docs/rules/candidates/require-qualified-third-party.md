# require-qualified-third-party

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | require-qualified-third-party |
| 対象 | 単一ファイル |

## 概要

サードパーティライブラリを `from ... import` で直接インポートしている場合に違反を検出します。`import module` 形式でモジュール名をインポートし、`module.name` の完全修飾名で使用することを要求します。

## 背景と意図

`from requests import get` のように名前を直接インポートすると、その名前がどのライブラリに由来するかがコード上から見えなくなります。外部依存の境界をコード中で明示することで、ライブラリへの依存箇所が一目で把握でき、依存関係の管理や変更時の影響範囲の特定が容易になります。また、名前空間の混在を避けることで、標準ライブラリや内部モジュールと同名のシンボルが衝突するリスクも低減できます。

`import module as alias` のようなエイリアスも同様の問題を引き起こします。エイリアスは元のモジュール名を隠蔽し、コードを読む際にエイリアスの定義箇所を追う必要が生じます。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `from {module} import {name}` はサードパーティライブラリの直接インポートである |
| reason | 外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある |
| suggestion | `import {module}` に書き換え、使用箇所を `{module}.{name}` 形式に修正する |

## 検出パターン

### 違反コード

```python
# サードパーティライブラリを from ... import で直接インポートしている
from gzip import open as gzip_open
from ijson import items

with gzip_open(file_path, "rt") as f:
    items_list = items(f, "item")
```

```python
# モジュールをエイリアスでインポートしている
import pydantic as pyd

class MyModel(pyd.BaseModel):
    name: str
```

### 準拠コード

```python
# モジュール名でインポートし、完全修飾名で使用している
import gzip
import ijson

with gzip.open(file_path, "rt") as f:
    items = ijson.items(f, "item")
```

```python
# エイリアスなしでモジュールをインポートしている
import pydantic

class MyModel(pydantic.BaseModel):
    name: str
```

## 検出の補足

このルールの最も難しい検出条件は「サードパーティライブラリかどうか」の判定です。

初期実装では、`from X import Y` パターンのうち、以下の2つを除外したものを違反とします。

- `sys.stdlib_module_names`（Python 3.10 以降）に含まれる標準ライブラリ（`os`、`sys`、`pathlib` 等）
- プロジェクトルートパッケージに属する内部モジュール

この方針には以下の限界があります。まず、Python 3.10 未満の環境では `sys.stdlib_module_names` が利用できないため、フォールバック手段が必要です。また、インストール済みパッケージを実行時に参照しない静的解析では、モジュールがサードパーティか否かを確実に判定できないケースがあります。さらに、相対インポート（`from . import utils`）は内部モジュールとして除外しますが、絶対インポートでプロジェクト内パッケージを参照する場合は設定による明示的な指定が必要です。

サブモジュールのインポートについては、`from package import SubModule` のように完全修飾名で使う前提のサブモジュールのインポートは違反としない可能性があります。`SubModule` がモジュールオブジェクト（クラスや関数ではない）である場合、`package.SubModule.method()` と等価な使用が可能であるためです。ただし、静的解析の時点でインポートされた名前がモジュールかどうかを確実に判別するのは困難なため、初期実装ではこのケースも違反として検出し、検出対象外の扱いは後続の実装で検討します。

エイリアス（`import module as alias`）の検出は、`from ... import` とは独立したパターンとして扱います。

## 既存ツールとの関係

Ruff はインポートの並び順や整形（`isort` 相当の `I` ルール群）はサポートしていますが、「サードパーティライブラリを完全修飾名で使用することを強制する」ルールは持っていません。Ruff の `TID252`（`from` インポートの禁止）は特定モジュールを対象とした設定ベースの制限であり、サードパーティ全体を対象とした使用パターンの強制は行いません。したがって、このルールは Ruff で代替できない検出であり、Paladin で扱う対象です。
