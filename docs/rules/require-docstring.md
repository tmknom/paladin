# require-docstring

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | require-docstring |
| 対象 | 単一ファイル |

## 概要

モジュールおよびクラスに docstring が存在することを要求します。モジュール docstring またはクラス docstring が存在しない場合に違反を検出します。

## 背景と意図

docstring はコードの「何をするか」を表明する唯一の公式な手段です。型アノテーションや命名が正確であっても、設計上の位置づけ・制約・責務の境界はコードから読み取れないことがほとんどです。

docstring が存在しない場合、以下の問題が生じます。

- **設計意図の欠如** — モジュールが「なぜここに存在するか」「どの層の責務を担うか」を表明できず、読み手が実装を全て読んで推測するしかなくなる
- **クラスの責務が不明確** — クラス docstring がないと、このクラスが何をするもので何をしないのかの境界が曖昧になる
- **コードレビューの効率低下** — docstring がないと、レビュアーが実装を読み切ってから意図を推測する必要があり、レビューコストが上がる

docstring の存在を自動検出することで、最低限の記述水準を機械的に保証できます。

## 診断メッセージ

### モジュール docstring がない場合

| フィールド | 内容 |
|-----------|------|
| message | `{path}` にモジュール docstring がありません |
| reason | モジュールの設計上の位置づけや制約を表明する手段がなくなります |
| suggestion | ファイル冒頭にモジュール docstring を追加してください |

### クラス docstring がない場合

| フィールド | 内容 |
|-----------|------|
| message | クラス `{class_name}` に docstring がありません |
| reason | クラスの責務・契約を表明する手段がなくなります |
| suggestion | クラス定義の直後に docstring を追加してください |

## 検出パターン

### 違反コード

```python
# モジュール docstring がない
import ast

class AstParser:
    # クラス docstring もない
    def parse(self, source: str) -> ast.Module:
        return ast.parse(source)
```

```python
"""モジュール docstring はある"""

import ast

class AstParser:
    # クラス docstring がない
    def parse(self, source: str) -> ast.Module:
        return ast.parse(source)
```

### 準拠コード

```python
"""AST解析層の入力担当。ソースコードを構文木に変換する薄いラッパー"""

import ast

class AstParser:
    """Python ソースコードを ast.Module に変換するパーサー"""

    def parse(self, source: str) -> ast.Module:
        return ast.parse(source)
```

## 検出の補足

### 検出ロジック

**モジュール docstring の検出:**

`ast.Module.body` の最初のステートメントが `ast.Expr` であり、その値が `ast.Constant` かつ型が `str` である場合に docstring ありと判定します。body が空の場合、または上記条件を満たさない場合に違反を報告します。

**クラス docstring の検出:**

`ast.ClassDef.body` の最初のステートメントに対して、モジュール docstring と同様の判定を行います。AST を再帰的に走査し、全ての `ClassDef` を対象とします（ネストしたクラスを含む）。

### 適用範囲

- モジュール docstring: プロダクションコード（`tests/` 配下を除く）の全 `.py` ファイルを対象とします。`__init__.py` も含みます
- クラス docstring: プロダクションコード（`tests/` 配下を除く）の全 `ClassDef` を対象とします
- テストファイル（`tests/` 配下）はモジュール docstring もクラス docstring も対象外とします

### 実質的なコードのないファイルの扱い

以下のファイルはモジュール docstring チェックをスキップします。

- ファイルの内容が空（または空白のみ）
- `__init__.py` で `__all__` の定義のみを含む場合はスキップしません（docstring を要求します）

### 報告の粒度

- モジュール docstring の欠如は1ファイルにつき1件（行番号は1行目）を報告します
- クラス docstring の欠如は各クラスにつき1件（`class` 文の行番号）を報告します

### 設定ファイル

このルールはデフォルトで有効です。特定のファイルやディレクトリを除外する場合は `per-file-ignores` または `[[tool.paladin.overrides]]` を使用します。

```toml
[tool.paladin.rules]
require-docstring = true
```

ディレクトリ別に無効化する場合の例。

```toml
[[tool.paladin.overrides]]
files = ["scripts/**"]

[tool.paladin.overrides.rules]
require-docstring = false
```

## 既存ツールとの関係

Ruff には `D100`（モジュール docstring の欠如）・`D101`（クラス docstring の欠如）等の pydocstyle ルールが存在します。ただし、Ruff の pydocstyle ルールは docstring のスタイル（Google/NumPy/reStructuredText 等のフォーマット規約）まで幅広く検査するため、設定の複雑さが増します。

Paladin の `require-docstring` は「docstring の存在有無」のみを検査するシンプルなルールとして位置づけます。スタイルの詳細な検査は行わず、最低限の記述水準の保証に特化します。
