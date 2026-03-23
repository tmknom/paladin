# no-cross-package-import

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-cross-package-import |
| 対象 | 複数ファイル |

## 概要

設定ファイルの `allow-dirs` に含まれないパッケージからのクロスパッケージインポートを禁止するルールです。`allow-dirs` に列挙されたディレクトリ配下のパッケージのモジュールはどこからでもインポート可能ですが、それ以外のパッケージのモジュールを別のパッケージからインポートしている場合に違反を検出します。

## 背景と意図

依存方向に制約がない状態では、パッケージ間の参照が無秩序に増加します。これは以下の問題を引き起こします。

- **アーキテクチャ境界の崩壊**: 「どのパッケージが何に依存してよいか」という設計上の意図が、コードベースに自動的に反映されない。意図しない依存が静かに蓄積される
- **変更影響範囲の拡大**: あるパッケージを変更したとき、そのパッケージを直接参照している別パッケージが意図せず壊れる。依存グラフが複雑になるほど影響範囲の特定が難しくなる
- **責務の混在**: 本来「他パッケージからインポートされることを想定しない」パッケージのモジュールが外部から参照されることで、そのモジュールが変更しにくくなる

`allow-dirs` に「他パッケージからインポートしてよいパッケージ」を明示することで、依存方向のアーキテクチャ制約を設定ファイルで宣言し、このルールで自動検証できます。

## 診断メッセージ

`import X` パターン:

| フィールド | 内容 |
|-----------|------|
| message | `import {module}` は許可されていないクロスパッケージインポートである |
| reason | `{module}` は `allow-dirs` に含まれないパッケージのモジュールであり、同一パッケージ内からのみインポート可能である |
| suggestion | `{module}` の利用を許可ディレクトリ配下に移動するか、`allow-dirs` にそのパッケージを追加してください |

`from X import Y` パターン:

| フィールド | 内容 |
|-----------|------|
| message | `from {module} import {name}` は許可されていないクロスパッケージインポートである |
| reason | `{module}` は `allow-dirs` に含まれないパッケージのモジュールであり、同一パッケージ内からのみインポート可能である |
| suggestion | `{module}` の利用を許可ディレクトリ配下に移動するか、`allow-dirs` にそのパッケージを追加してください |

## 検出パターン

### 違反コード

```python
# src/paladin/view/context.py — allow-dirs に含まれないパッケージを別パッケージからインポート
from paladin.check import OutputFormat  # 違反: paladin.check は allow-dirs に含まれない
```

```python
# src/paladin/list/formatter.py — allow-dirs に含まれないパッケージを別パッケージからインポート
from paladin.check.formatter import CheckFormatterFactory  # 違反: paladin.check は allow-dirs に含まれない
```

### 準拠コード

```python
# src/paladin/check/orchestrator.py — allow-dirs に含まれるパッケージをインポート
from paladin.rule import RuleMeta, Violation  # 準拠: paladin.rule は allow-dirs に含まれる
```

```python
# src/paladin/view/context.py — 同一パッケージ内のモジュールをインポート
from paladin.view.types import ViewResult  # 準拠: 同一パッケージ内のインポート
```

## 検出の補足

### 設定ファイル

このルールは `allow-dirs` パラメータで、他パッケージからインポートしてよいディレクトリを指定します。

```toml
[tool.paladin.rule.no-cross-package-import]
allow-dirs = ["src/paladin/foundation/", "src/paladin/protocol/", "src/paladin/rule/"]
```

- `allow-dirs` の各要素は `pyproject.toml` からの相対パスとして解釈される。末尾の `/` の有無によらずディレクトリとして扱う
- `allow-dirs` に含まれるパッケージのモジュールは、どこからでもインポート可能
- `allow-dirs` に含まれないパッケージのモジュールは、同一パッケージ内からのみインポート可能
- `allow-dirs` が未指定の場合、すべてのファイルでクロスパッケージインポートを禁止する
- `no-third-party-import` にも `allow-dirs` があるが、TOML のルール別セクションでスコープされるため衝突しない

### 検出ロジック

1. `prepare()` でルートパッケージを自動導出する（`PackageResolver` を再利用）
2. 各ファイルの AST を走査し、`ast.Import` / `ast.ImportFrom` ノードを収集する
3. 相対インポート（`level >= 1`）は内部モジュールであるため対象外とする
4. 標準ライブラリ（`sys.stdlib_module_names`）およびサードパーティのインポートは対象外とする
5. インポート先モジュールがルートパッケージに属さない場合は対象外とする
6. `PackageResolver.resolve_package_key()` でインポート元とインポート先のパッケージキー（先頭2セグメント）を比較し、一致する場合は同一パッケージとして対象外とする
7. インポート先パッケージのファイルパスが `allow-dirs` のいずれかに前方一致する場合は対象外とする
8. 上記のいずれにも該当しなければ違反として報告する

### エントリーポイントの除外

トップレベルに `def main()` が定義されているファイルはエントリーポイントとして扱い、違反を報告しません。エントリーポイントは複数パッケージの協調を必要とする性質上、クロスパッケージインポートが不可避であるためです。

### 同一パッケージの定義

同一パッケージかどうかの判定は `PackageResolver.resolve_package_key()` を用います。モジュールパスの先頭2セグメント（例: `paladin.check`）が一致する場合を同一パッケージとして扱います。これにより `paladin.check.orchestrator` から `paladin.check.formatter` へのインポートは違反になりません。

### テストファイルのマッピング

`tests/` 配下のテストファイルは、対応するプロダクションパッケージと同一視します。ディレクトリ名から `test_` プレフィックスを除去してプロダクションパッケージを算出します。

例: `tests/unit/test_check/test_orchestrator.py` は `paladin.check` パッケージと同一視されます。このため、このファイルから `paladin.check.formatter` をインポートしても違反になりません。一方、`paladin.view.formatter` のインポートは異なるパッケージからのインポートとして違反になります。

### 関連ルールとの差分

| ルール | 制約対象 | 本ルールとの関係 |
|--------|---------|----------------|
| `no-cross-package-reexport` | `__all__` での再エクスポート | 本ルールはインポート自体を制約するより広いスコープ。再エクスポートの前段となるインポートも検出できる |
| `no-direct-internal-import` | パッケージ内部モジュールへの直接アクセス | 本ルールはパッケージ間の依存方向を制約する。`no-direct-internal-import` はパッケージの公開 API を迂回する内部アクセスを制約する |
| `no-third-party-import` | サードパーティのインポート場所 | 本ルールは自プロジェクト内パッケージ間の依存方向を制約する。両ルールは補完的に機能する |

## 既存ツールとの関係

Ruff にはパッケージ間の依存方向を制約する機能はありません。`TID252`（`banned-module-level-imports`）は特定モジュールを禁止リストで管理できますが、「特定パッケージからのインポートは許可し、それ以外は禁止する」という `allow-dirs` ベースの条件付き制御はできません。

Pylint にもディレクトリ単位で依存方向を制約する仕組みはありません。

プロジェクト内パッケージ間の依存方向というアーキテクチャ制約の検証は、既存のリンターでは扱われていない領域であり、Paladin で独自に扱います。
