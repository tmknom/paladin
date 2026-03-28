# rule 設計書

## 1. 設計の目的と背景

### システム構成

`rule` モジュールは、Pythonソースコードを静的解析するルールエンジンの中核を担うドメイン層である。
ソースファイル群（`SourceFiles`）を入力として受け取り、登録済みの全ルールを適用して、違反の集合（`Violations`）を出力する。
上位モジュール（`check`）は `RuleSet` および `RuleSetFactory` を通じてこのドメイン層を利用する。

### 設計方針

- **Protocol による抽象化**: ルール具象クラスへの直接依存を排除し、追加時の変更を局所化する
- **値オブジェクトによる不変性の保証**: ソースファイル・違反・メタ情報はすべて不変な値オブジェクトとして定義する
- **2種類のルール実行モデル**: 単一ファイルルール（`Rule`）と複数ファイルルール（`MultiFileRule`）を明確に分離する
- **事前準備フェーズの分離**: 複数ファイルの情報を必要とするルールは `PreparableRule` で準備フェーズを分離する
- **ドメインサービスによる責務の分離**: パッケージ解決・`__all__` 抽出といった共通ロジックを独立したサービスクラスに切り出す

---

## 2. 設計の全体像

### 2.1 アーキテクチャパターン

- **Protocol パターン**: `Rule` / `MultiFileRule` / `PreparableRule` を Protocol で定義し、具象クラスへの依存を排除
- **ファクトリーパターン**: `RuleSetFactory` がプロダクション用のデフォルトルール一式を生成し、設定値の注入も担う
- **値オブジェクト**: `SourceFile` / `SourceFiles` / `Violation` / `Violations` / `RuleMeta` はすべて `@dataclass(frozen=True)` による不変オブジェクト
- **ドメインサービス**: `PackageResolver` / `OwnPackageResolver` / `AllExportsExtractor` は純粋なドメインロジックを提供

### 2.2 外部システム依存

- Python 標準ライブラリの `ast` モジュールによる AST 解析
- `sys.stdlib_module_names` による標準ライブラリ判定
- ファイルシステム参照（`NoDirectInternalImportRule` のサブパッケージ検出のみ）

### 2.3 主要コンポーネント

| コンポーネント | 種別 | 責務 |
|---|---|---|
| `Rule` | Protocol | 単一ファイルルールのインターフェース |
| `MultiFileRule` | Protocol | 複数ファイルルールのインターフェース |
| `PreparableRule` | Protocol | 実行前準備が必要なルールのインターフェース |
| `RuleSet` | クラス | ルールの管理・一括実行・一覧・検索 |
| `RuleSetFactory` | クラス | プロダクション用デフォルトルール一式の生成 |
| `RuleMeta` | 値オブジェクト | ルールID・名称・概要・意図・診断ガイダンス・改善提案の保持 |
| `SourceFile` | 値オブジェクト | 単一Pythonソースファイルの情報（パス・AST・ソーステキスト）の保持 |
| `SourceFiles` | 値オブジェクト | 複数ソースファイルの集約 |
| `Violation` | 値オブジェクト | 単一違反情報（位置・ルール・メッセージ等）の保持 |
| `Violations` | 値オブジェクト | 複数違反の集約 |
| `OverrideEntry` | 値オブジェクト | `[[tool.paladin.overrides]]` の単一エントリ |
| `PerFileIgnoreEntry` | 値オブジェクト | `per-file-ignores` の単一エントリ |
| `PackageResolver` | ドメインサービス | ファイルパスからパッケージ名の解決 |
| `OwnPackageResolver` | ドメインサービス | ファイルが属する自パッケージセットの解決 |
| `AllExportsExtractor` | ドメインサービス | `__all__` シンボルの抽出 |
| `ImportStatement` 等 | 値オブジェクト群 | AST インポートノードのラップと振る舞いのカプセル化 |

### 2.4 処理フロー概略

1. `RuleSetFactory.create()` でルール一式と設定値を組み立て `RuleSet` を生成する
2. `RuleSet.run()` が `PreparableRule` 実装ルールに `prepare()` を呼び出す（事前準備）
3. 各ソースファイルに対して単一ファイルルールを実行する（無効化IDを参照してスキップ）
4. `MultiFileRule` を実行する（全ファイルを対象）
5. 収集した違反を `Violations` にまとめて返す

---

## 3. 重要な設計判断

### 3.1 Rule と MultiFileRule の分離

ルール実行モデルを「単一ファイル」と「複数ファイル」に明示的に分離する。

`Rule` は `check(source_file: SourceFile)` を、`MultiFileRule` は `check(source_files: SourceFiles)` を持つ別の Protocol として定義する。`RuleSet` は両者を別々に保持し、単一ファイルループと複数ファイル実行を分けて処理する。

代替案として「1つの Protocol に統一して引数を使い分ける案」や「`check()` を常に `SourceFiles` で受け取る案」もあったが、前者は型の表現力が下がり呼び出し側が引数の型を意識する必要が生じる。後者は単一ファイルルールがファイルループを自前で行う必要があり責務が分散する。Protocol が2つに増えるトレードオフはあるが、型安全性とルール実装の明確化を優先した。

### 3.2 PreparableRule による事前準備フェーズ

全ファイルの情報を先に集約してから各ファイルを検査する必要があるルール（パッケージ解決など）のために、単一ファイルループの前に準備を完了できる仕組みを設ける。

`PreparableRule` Protocol を別途定義し、`RuleSet.run()` が `isinstance()` チェックで実装クラスを検出して `prepare()` を呼ぶ。

`MultiFileRule` に統合する案や、コンストラクタで `source_files` を受け取る案も検討したが、前者は単一ファイルループの外で事前集計しキャッシュする用途には `MultiFileRule` が不向きで実行フローが複雑になる。後者は `RuleSetFactory` の責務が肥大化し毎回新規インスタンスが必要になる。Protocol を分離することで準備が不要なルールへの影響をゼロにできる。

### 3.3 Protocol による抽象化（継承回避）

ルール具象クラスが `Rule` 基底クラスを継承する設計を避け、Protocol による構造的部分型を採用する。

`@runtime_checkable` な Protocol として `Rule` / `MultiFileRule` / `PreparableRule` を定義する。具象ルールは Protocol を実装するが、明示的な継承は不要。

抽象基底クラス（ABC）による継承では各ルールが基底クラスに依存し、基底クラス変更時の影響範囲が広がる。Protocol を採用することで、新規ルール追加時に既存の基底クラスを変更せず、独立したルールクラスを定義するだけで追加できる。

### 3.4 PackageResolver と OwnPackageResolver の分離

ファイルパスからパッケージキーを解決するロジック（`PackageResolver`）と、テストファイルに対応するプロダクションパッケージの同一視ロジック（`OwnPackageResolver`）を分離する。

`PackageResolver` は `src/` レイアウトと `tests/` を考慮したパッケージ解決のみを担い、`OwnPackageResolver` はテストファイルのディレクトリ名（`test_view/` → `paladin.view`）からの対応プロダクションパッケージ導出を担う。

クロスパッケージインポート系ルールと内部インポートルールで共通の判定ロジックを再利用できるとともに、テスト固有の変換ロジックを分離することで `PackageResolver` の責務を明確化できる。

### 3.5 ルールオプションの注入（コンストラクタ経由）

可変オプション（`allow-dirs`・`max-lines` 等）をルールのコンストラクタで受け取る設計にする。

`RuleSetFactory.create()` が設定値を解析し、各ルールのコンストラクタに注入する。ルール自身は設定解析ロジックを持たない。

設定解析をルール内に持つ案ではルールと設定フォーマットが密結合になり設定スキーマ変更時の影響が広がる。ルールクラスを純粋なドメインロジックに集中させ、設定の解釈責務を `RuleSetFactory` に一元化できる。

### 3.6 RuleMeta による違反生成の一元化

違反生成をルールメタ情報と結びつけることで、各ルールが `rule_id` / `rule_name` を繰り返し参照しなくて済むようにする。

`RuleMeta` 値オブジェクト自身に `create_violation_at(location, message, reason, suggestion)` を持たせ、`Violation` を生成する責務を与える。

これによりルール ID・ルール名を各違反生成コードに重複記述することを防ぎ、`RuleMeta` を起点に `Violation` が生成される流れを明確化できる。

---

## 4. アーキテクチャ概要

### 4.1 レイヤー構造とファイルレイアウト

```
src/paladin/rule/
├── __init__.py              # 公開 API（__all__ で管理）
│
├── [インターフェース層]
│   └── protocol.py          # Rule / MultiFileRule / PreparableRule Protocol
│
├── [型・値オブジェクト層]
│   ├── types.py             # SourceFile / SourceFiles / Violation / Violations
│   │                        # RuleMeta / OverrideEntry / PerFileIgnoreEntry
│   └── import_statement.py  # ModulePath / ImportStatement / AbsoluteFromImport
│                            # ImportedName / SourceLocation
│
├── [実行管理層]
│   ├── rule_set.py          # RuleSet（複数ルールの管理・実行）
│   └── rule_set_factory.py  # RuleSetFactory（デフォルトルール一式の生成）
│
├── [ドメインサービス層]
│   ├── package_resolver.py      # PackageResolver（パッケージキー解決）
│   ├── own_package_resolver.py  # OwnPackageResolver（自パッケージ解決）
│   └── all_exports_extractor.py # AllExportsExtractor / AllExports
│
└── [ルール実装層]
    ├── require_all_export.py         # require-all-export
    ├── no_relative_import.py         # no-relative-import
    ├── no_local_import.py            # no-local-import
    ├── no_non_init_all.py            # no-non-init-all
    ├── no_cross_package_reexport.py  # no-cross-package-reexport
    ├── no_mock_usage.py              # no-mock-usage
    ├── no_deep_nesting.py            # no-deep-nesting
    ├── no_third_party_import.py      # no-third-party-import（PreparableRule）
    ├── no_cross_package_import.py    # no-cross-package-import（PreparableRule）
    ├── require_qualified_third_party.py # require-qualified-third-party（PreparableRule）
    ├── max_method_length.py          # max-method-length
    ├── max_class_length.py           # max-class-length
    ├── max_file_length.py            # max-file-length
    ├── no_direct_internal_import.py  # no-direct-internal-import（MultiFileRule + PreparableRule）
    ├── no_unused_export.py           # no-unused-export（MultiFileRule + PreparableRule）
    └── no_testing_test_code.py       # no-testing-test-code（MultiFileRule）
```

依存の方向:

```
rule_set_factory.py
    └─▶ rule_set.py
    └─▶ [各ルール実装層]
             └─▶ ドメインサービス層（PackageResolver / AllExportsExtractor 等）
             └─▶ 型・値オブジェクト層（SourceFile / RuleMeta / Violation 等）
             └─▶ インターフェース層（Rule / MultiFileRule Protocol）
```

### 4.2 処理フロー

#### 通常のルール実行（RuleSet.run）

```
RuleSet.run(source_files, disabled_rule_ids, per_file_disabled)
  │
  ├─[1] PreparableRule の事前準備
  │       for rule in (rules + multi_file_rules):
  │           if isinstance(rule, PreparableRule):
  │               rule.prepare(source_files)
  │
  ├─[2] 単一ファイルループ
  │       for source_file in source_files:
  │           effective_disabled = per_file_disabled.get(file_path, disabled_rule_ids)
  │           for rule in rules:
  │               if rule_id in effective_disabled: skip
  │               violations += rule.check(source_file)
  │
  └─[3] 複数ファイルルール実行
          for multi_rule in multi_file_rules:
              if rule_id in disabled_rule_ids: skip
              violations += multi_rule.check(source_files)
                  │
                  └─▶ Violations(items=tuple(violations))
```

#### パッケージ解決フロー（PackageResolver）

```
ファイルパス
  │
  ├─ dir_parts から src/ または tests/ のアンカーを検出
  ├─ アンカーより後のパスセグメントをパッケージ部分として使用
  │
  ├─ resolve_package_key()    → 先頭2セグメント（例: "paladin.check"）
  └─ resolve_exact_package_path() → 全セグメント（例: "paladin.foundation.model"）
```

---

## 5. 重要な制約と注意点

### 5.1 src レイアウト前提

`PackageResolver` は `src/` ディレクトリをアンカーとしてパッケージセグメントを決定する設計になっている。
`src/` を使わないフラットレイアウトでは `NON_PACKAGE_DIRS` のフォールバック処理が使われるが、主要ユースケースは `src/` 配置を前提とする。

### 5.2 MultiFileRule の per-file 無効化非対応

`RuleSet.run()` の `per_file_disabled` は単一ファイルルールにのみ適用される。
`MultiFileRule` の無効化はグローバルな `disabled_rule_ids` のみで制御される。

### 5.3 ファイルシステム参照（NoDirectInternalImportRule）

`NoDirectInternalImportRule` はサブパッケージ存在確認のために実行時にファイルシステムを参照する。
これは他のルールと異なる副作用であり、テスト時にはファイルシステムの状態に依存するため、テスト用ディレクトリ構造を用意するか、サブパッケージ検出が不要なケースで検証する必要がある。

### 5.4 パッケージキーの先頭2セグメント制約

`resolve_package_key()` は常に先頭2セグメント（例: `paladin.check`）を返す。
3階層以上のネストしたパッケージ（`paladin.foundation.model` 等）を区別する場合は `resolve_exact_package_path()` を使う必要がある。

---

## 6. 将来の拡張性

### 6.1 想定される拡張ポイント

- **新規ルールの追加**: 新しいルールクラスを作成し、`RuleSetFactory.create()` に追加するだけで組み込める
- **新しいルール実行モデル**: Protocol を追加し、`RuleSet.run()` に対応する実行ブランチを追加する
- **設定オプションの追加**: `RuleSetFactory._extract_*` メソッドを拡張することでルール固有の設定値を追加できる

### 6.2 拡張時の注意点

- 新規ルールを追加した場合、`RuleSetFactory.create()` のルール一式に追加するとともに、
  `list` / `view` モジュールのプロバイダーが期待するルール数のテストを更新する必要がある
- `PreparableRule` と `Rule`（または `MultiFileRule`）を両方実装するルールでは、
  `prepare()` で初期化した内部状態を `check()` で参照するため、`prepare()` 呼び出し前の `check()` 呼び出しが無効な状態を返すことに注意する

---

## 7. 関連ドキュメント

- [rule 要件定義](./requirements.md)
