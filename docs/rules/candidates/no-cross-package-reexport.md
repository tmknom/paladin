# no-cross-package-reexport

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-cross-package-reexport |
| 対象 | 単一ファイル |

## 概要

別パッケージのシンボルを自パッケージの `__all__` で再エクスポートすることを禁止するルールです。`__init__.py` の `__all__` に自パッケージ以外で定義されたシンボルが含まれている場合に違反を検出します。

## 背景と意図

`__init__.py` の `__all__` はそのパッケージの公開インタフェースを定義するものです。別パッケージのシンボルを `__all__` に含めると、以下の問題が生じます。

- パッケージの利用者が、実際の定義元を知らずに誤ったパッケージに依存する。本来 `paladin.lint` を参照すべきところを `paladin.check` 経由でインポートしてしまう
- 定義元パッケージと再エクスポート元パッケージの2か所で同一シンボルが公開APIとして存在し、利用者がどちらを使えばよいか判断できなくなる
- 別パッケージの内部変更（シンボルの移動・削除・リネーム）が、再エクスポートを通じて意図せず波及する
- パッケージの責務が不明確になり、依存関係グラフが不必要に複雑になる

`__all__` には自パッケージ内で定義したシンボルのみを列挙することで、パッケージ境界を明確に保ち、各パッケージが自身の公開インタフェースに責任を持つ設計を維持できます。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `__all__` に別パッケージのシンボル `{name}` が含まれている（定義元: `{source_package}`） |
| reason | `{source_package}` で定義されたシンボルを `{current_package}` の公開 API として再エクスポートすると、パッケージ境界が曖昧になる |
| suggestion | `{name}` を `__all__` から削除し、利用者が `from {source_package} import {name}` を直接使用するよう誘導してください |

## 検出パターン

### 違反コード

```python
# paladin/check/__init__.py
from paladin.check.context import CheckContext
from paladin.check.result import CheckReport
from paladin.lint import RuleMeta, Violation, Violations  # 別パッケージからのインポート

__all__ = [
    "CheckContext",
    "CheckReport",
    "RuleMeta",    # 違反: paladin.lint で定義されたシンボル
    "Violation",   # 違反: paladin.lint で定義されたシンボル
    "Violations",  # 違反: paladin.lint で定義されたシンボル
]
```

### 準拠コード

```python
# paladin/check/__init__.py
from paladin.check.context import CheckContext
from paladin.check.result import CheckReport

__all__ = [
    "CheckContext",  # 自パッケージ内で定義されたシンボルのみ
    "CheckReport",
]
```

```python
# paladin/lint/__init__.py
from paladin.lint.types import RuleMeta, Violation, Violations

__all__ = [
    "RuleMeta",    # 自パッケージ内で定義されたシンボル
    "Violation",
    "Violations",
]
```

## 検出の補足

このルールは `__init__.py` のみを対象とします。通常のモジュールファイル（`__init__.py` 以外）における `__all__` は対象外です。

検出のロジックは以下のとおりです。

- `__init__.py` に含まれる `from X import Y` 文を収集し、各シンボルの定義元パッケージを特定する
- `__all__` に列挙されているシンボルのうち、現在のパッケージ外で定義されたものを違反として報告する
- 定義元パッケージの判定は、インポート元のモジュールパス（`from paladin.lint import ...` であれば `paladin.lint`）から行う

自パッケージ内のサブモジュールや子パッケージからのインポートは準拠です（`from paladin.check.context import CheckContext` のように、現在のパッケージのプレフィックスを持つインポートは違反になりません）。

## 既存ツールとの関係

Ruff には `__all__` への別パッケージシンボルの混入を検出するルールはありません。`F401`（未使用インポート）や `PLC0414`（再エクスポートの明示化）は別の観点のルールであり、パッケージ境界の越境を検出するものではありません。

パッケージの責務分離という設計上の意図を検出するルールとして、Paladin で独自に扱います。
