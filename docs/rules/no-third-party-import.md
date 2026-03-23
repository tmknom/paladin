# no-third-party-import

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-third-party-import |
| 対象 | 単一ファイル |

## 概要

事前に許可したディレクトリ以外でのサードパーティライブラリのインポートを禁止するルールです。設定ファイルで指定した `allow-dirs` 配下のファイルでのみサードパーティライブラリの利用を許容し、それ以外のディレクトリで `import X` や `from X import Y` の形式でサードパーティをインポートしている場合に違反を検出します。

## 背景と意図

サードパーティライブラリはプロジェクト全体に散在しがちです。どのモジュールからでも自由にサードパーティをインポートできる状態は、以下の問題を引き起こします。

- **依存関係の不透明化**: サードパーティライブラリがプロジェクトのどこで使われているかを把握するために、全ファイルを走査しなければならない。依存関係の影響範囲を特定するコストが増大する
- **ライブラリ置換の困難さ**: サードパーティライブラリを別のライブラリに置き換える場合、利用箇所がプロジェクト全体に分散していると修正範囲が広がり、移行コストが高くなる
- **アーキテクチャ境界の崩壊**: 特定の基盤レイヤーにサードパーティの利用を集約する設計を採用しても、制約が自動的に検証されなければ徐々に侵食される

サードパーティライブラリの利用を特定のディレクトリ（例えば `foundation/` のような基盤レイヤー）に集約することで、外部依存の境界が明確になり、ライブラリの変更や置換の影響範囲を局所化できます。このルールは、その集約方針を自動的に検証する仕組みを提供します。

## 診断メッセージ

`import X` パターン:

| フィールド | 内容 |
|-----------|------|
| message | `import {module}` は許可ディレクトリ外でのサードパーティライブラリのインポートである |
| reason | サードパーティライブラリの利用は `allow-dirs` で指定されたディレクトリに集約する必要がある |
| suggestion | `{module}` の利用を許可ディレクトリ配下に移動するか、ラッパーモジュール経由でアクセスしてください |

`from X import Y` パターン:

| フィールド | 内容 |
|-----------|------|
| message | `from {module} import {name}` は許可ディレクトリ外でのサードパーティライブラリのインポートである |
| reason | サードパーティライブラリの利用は `allow-dirs` で指定されたディレクトリに集約する必要がある |
| suggestion | `{module}` の利用を許可ディレクトリ配下に移動するか、ラッパーモジュール経由でアクセスしてください |

## 検出パターン

### 違反コード

```python
# src/paladin/config/env_var.py — 許可ディレクトリ外でサードパーティをインポート
import pydantic_settings  # 違反: allow-dirs に含まれないディレクトリ

class EnvVarConfig(pydantic_settings.BaseSettings):
    log_level: str = "WARNING"
```

```python
# src/paladin/transform/types.py — 許可ディレクトリ外でサードパーティをインポート
from pydantic import BaseModel  # 違反: allow-dirs に含まれないディレクトリ

class TransformResult(BaseModel):
    output: str
```

### 準拠コード

```python
# src/paladin/foundation/model/base.py — 許可ディレクトリ内でのインポート
import pydantic  # 準拠: allow-dirs に "src/paladin/foundation/" が含まれている

class CoreModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)
```

```python
# src/paladin/config/env_var.py — 内部モジュール経由でアクセスする修正例
from paladin.foundation.model import CoreSettings, SettingsConfigDict  # 準拠: 内部モジュール経由

class EnvVarConfig(CoreSettings):
    model_config = SettingsConfigDict(env_prefix="EXAMPLE_")
    log_level: str = "WARNING"
```

## 検出の補足

### 設定ファイル

このルールは `allow-dirs` パラメータで許可ディレクトリを指定します。

```toml
[tool.paladin.rule.no-third-party-import]
allow-dirs = ["src/paladin/foundation/"]
```

`allow-dirs` の各要素は `pyproject.toml` からの相対パスとして解釈されます。末尾の `/` の有無によらず、ディレクトリとして扱います。`allow-dirs` が未指定の場合、すべてのファイルでサードパーティライブラリのインポートを禁止します。

### サードパーティかどうかの判定

サードパーティライブラリの判定は、既存の `require-qualified-third-party` ルールと同じ方式を採用します。

- `sys.stdlib_module_names`（Python 3.10 以降）に含まれる標準ライブラリは除外する
- プロジェクトルートパッケージに属する内部モジュールは除外する
- 上記に該当しないモジュールをサードパーティとして判定する

### 検出ロジック

1. ファイルパスが `allow-dirs` のいずれかに前方一致するか判定する
2. `allow-dirs` 内のファイルはすべてのインポートを許可する（検査をスキップする）
3. `allow-dirs` 外のファイルについて、AST を走査し以下を検出する
    - `ast.Import` ノード: `import X` 形式で、`X` のトップレベル名がサードパーティに該当する場合に違反
    - `ast.ImportFrom` ノード: `from X import Y` 形式で、`X` のトップレベル名がサードパーティに該当する場合に違反
4. 相対インポート（`level >= 1`）は内部モジュールであるため検出対象外とする

### 対象外のパターン

以下は違反として報告しません。

- `allow-dirs` に指定されたディレクトリ配下のファイル
- 標準ライブラリのインポート（`os`、`sys`、`pathlib` 等）
- プロジェクト内部モジュールのインポート
- 相対インポート（`from . import utils` 等）

### require-qualified-third-party との関係

`require-qualified-third-party` は「サードパーティライブラリのインポート形式」を制約するルールであり、`from X import Y` を禁止して `import X` の完全修飾名を要求します。

`no-third-party-import` は「サードパーティライブラリをインポートする場所」を制約するルールであり、`allow-dirs` 外では `import X` も `from X import Y` もいずれも禁止します。

両ルールを併用する場合、`allow-dirs` 内のファイルには `require-qualified-third-party` が適用され、完全修飾名での利用が要求されます。`allow-dirs` 外のファイルではそもそもサードパーティのインポートが禁止されるため、`require-qualified-third-party` の検出対象にもなりません。

## 既存ツールとの関係

Ruff の `TID252`（`banned-module-level-imports`）は特定モジュールのインポートを禁止リストで管理する機能を持ちますが、「許可ディレクトリ内では許可する」という条件付きの制御はできません。Ruff の `per-file-ignores` と組み合わせることで近い挙動は実現可能ですが、サードパーティ全体を対象とした自動判定と許可ディレクトリの組み合わせは Ruff では表現できません。

Pylint にもディレクトリ単位でインポート制約を切り替える仕組みはありません。

サードパーティライブラリの利用箇所を特定ディレクトリに限定するというアーキテクチャ制約の検証は、既存のリンターでは扱われていない領域であり、Paladin で独自に扱います。
