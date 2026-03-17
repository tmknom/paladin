# no-mock-usage

## メタ情報

| 項目 | 値 |
|------|-----|
| ルールID | no-mock-usage |
| 対象 | 単一ファイル |

## 概要

`unittest.mock.Mock` / `unittest.mock.MagicMock` の使用を禁止するルールです。テストコードおよびプロダクションコードのいずれにおいても、これらのモックオブジェクトをインポートまたは呼び出している場合に違反を検出します。

## 背景と意図

テストにおける依存の置き換えには、主に Mock パターンと Fake パターンの2つがあります。

**Mock パターン**（このルールが禁止する対象）は、`unittest.mock.Mock` や `MagicMock` を使って、任意のオブジェクトを動的に模倣します。呼び出しの有無・引数・戻り値を後から検証できる一方で、以下の問題が生じます。

- インターフェースを静的に表現しないため、テスト対象のシグネチャ変更を型チェッカーが検出できない
- `spec=` を指定しない場合、存在しないメソッドへの呼び出しも通過し、テストが実装の乖離を見逃す
- テストコード内に「期待する呼び出し方」を記述するため、実装の詳細に依存した脆弱なテストになりやすい
- テストの意図が `assert_called_once_with` のような Mock 固有の検証コードに埋もれ、可読性が低下する

**Fake パターン**（このルールが推奨する代替）は、Protocol を満たすシンプルな代替実装をクラスとして定義します。

- Protocol を実装するため、型チェッカーによるインターフェース整合性の検証が効く
- インターフェースの変更があれば Fake 側でコンパイルエラーが発生し、テストの陳腐化を防ぐ
- Fake クラスはテスト入力に対して決定的に動作するため、テストの振る舞いが明確

`Mock` / `MagicMock` を使わず Fake パターンを一貫して採用することで、型安全なテストとインターフェース変更への耐性を両立できます。

## 診断メッセージ

| フィールド | 内容 |
|-----------|------|
| message | `{name}` のインポートは禁止されています |
| reason | Mock/MagicMock は型チェッカーによる検証が効かず、インターフェース変更を見逃す可能性がある |
| suggestion | Protocol を満たす Fake クラスを定義して代替してください |

## 検出パターン

### 違反コード

```python
# tests/unit/test_check/test_orchestrator.py
from unittest.mock import Mock, MagicMock  # 違反: Mock/MagicMock のインポート

def test_orchestrator():
    rule = Mock(spec=Rule)          # 違反: Mock の使用
    runner = MagicMock(spec=RuleSet)  # 違反: MagicMock の使用
    ...
```

```python
# tests/unit/test_check/test_orchestrator.py
import unittest.mock  # 違反: unittest.mock のインポート

def test_something():
    obj = unittest.mock.Mock()  # 違反: Mock の使用
```

### 準拠コード

```python
# tests/unit/fakes/fake_rule.py — Protocol を満たす Fake クラスを定義
from paladin.rule.protocol import Rule
from paladin.rule.types import RuleMeta, SourceFile, Violation

class FakeRule:
    def __init__(self, violations: tuple[Violation, ...] = ()) -> None:
        self._meta = RuleMeta(
            rule_id="fake-rule",
            rule_name="Fake Rule",
            summary="Testing fake",
            intent="",
            guidance="",
            suggestion="",
        )
        self._violations = violations

    @property
    def meta(self) -> RuleMeta:
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        return self._violations
```

```python
# tests/unit/test_check/test_orchestrator.py
from tests.unit.fakes.fake_rule import FakeRule  # 準拠: Fake クラスを使用

def test_orchestrator():
    rule = FakeRule(violations=())  # 準拠: Fake を直接インスタンス化
    ...
```

```python
# tests/integration/test_integration.py — pytest.MonkeyPatch は許容
def test_with_external_api(monkeypatch):
    monkeypatch.setattr("requests.get", lambda url, **kwargs: ...)  # 準拠: monkeypatch は許容
```

## 検出の補足

### 対象外のパターン

以下は違反として報告しません。

- `pytest.MonkeyPatch` または `monkeypatch` fixture の使用: 外部ネットワーク・サードパーティ API の差し替えには `monkeypatch` が適切であり、許容します
- `from unittest.mock import patch` を `monkeypatch` の代替として使う場合も、`patch` はデコレーターや `with` ブロックとして使われることが多く、検出対象に含めるかどうかはプロジェクトの方針に依存します

### 検出ロジック

- `ast.ImportFrom` で `module` が `"unittest.mock"` であり、`names` に `"Mock"` または `"MagicMock"` が含まれるインポートを検出する
- `ast.Import` で `names` に `"unittest.mock"` が含まれるインポートを検出する
- インポート文の存在を違反とする（呼び出しの有無は問わない）

### 適用範囲

このルールはテストファイル（`tests/` 配下）だけでなく、プロダクションコード（`src/` 配下）にも適用します。プロダクションコードで Mock を使うことはさらに問題が大きいためです。

## 既存ツールとの関係

Ruff には `unittest.mock.Mock` / `MagicMock` の使用を禁止するルールはありません。`S106`（パスワードハードコード検出）や `FBT`（Boolean パラメーター検出）など、特定の設計アンチパターンを検出するルールはありますが、Mock 使用禁止は対象外です。

Pylint にも直接該当するルールは存在しません。Mock の使用が型安全なテストパターン（Fake パターン）に反するという設計上の観点は、既存のリンターでは扱われていない領域であり、Paladin で独自に扱います。
