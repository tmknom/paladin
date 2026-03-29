# rule モジュール基本設計

[rule モジュール要件定義](./requirements.md) に基づいた基本設計を説明します。

## アーキテクチャパターン

[Python アーキテクチャ設計](../../design/architecture.md) に記載のパターンを採用しています。

| パターン | 適用箇所 | 目的 |
|---|---|---|
| Protocol | `Rule` / `MultiFileRule` / `PreparableRule` | ルール具象クラスへの直接依存を排除し、追加時の変更を局所化する |
| ファクトリー | `RuleSetFactory` | プロダクション用のデフォルトルール一式を生成し、設定値の注入を担う |
| 値オブジェクト | `SourceFile` / `Violation` / `RuleMeta` 等 | 不変性を保証し、検査データの安全な受け渡しを実現する |
| ドメインサービス | `PackageResolver` / `OwnPackageResolver` / `AllExportsExtractor` | パッケージ解決・`__all__` 抽出などの共通ドメインロジックを独立させる |

## コンポーネント構成

### 主要コンポーネント

| コンポーネント | 種別 | 責務 |
|---|---|---|
| `Rule` | Protocol | 単一ファイルルールのインターフェース |
| `MultiFileRule` | Protocol | 複数ファイルルールのインターフェース |
| `PreparableRule` | Protocol | 実行前準備が必要なルールのインターフェース |
| `RuleSet` | クラス | ルールの管理・一括実行・一覧・検索 |
| `RuleSetFactory` | クラス | プロダクション用デフォルトルール一式の生成 |
| `RuleMeta` | 値オブジェクト | ルール ID・名称・概要・意図・診断ガイダンス・改善提案の保持 |
| `SourceFile` | 値オブジェクト | 単一 Python ソースファイルの情報（パス・AST・ソーステキスト）の保持 |
| `SourceFiles` | 値オブジェクト | 複数ソースファイルの集約 |
| `Violation` | 値オブジェクト | 単一違反情報（位置・ルール・メッセージ等）の保持 |
| `Violations` | 値オブジェクト | 複数違反の集約 |
| `OverrideEntry` | 値オブジェクト | `[[tool.paladin.overrides]]` の単一エントリ |
| `PerFileIgnoreEntry` | 値オブジェクト | `per-file-ignores` の単一エントリ |
| `PackageResolver` | ドメインサービス | ファイルパスからパッケージ名の解決 |
| `OwnPackageResolver` | ドメインサービス | ファイルが属する自パッケージセットの解決 |
| `AllExportsExtractor` | ドメインサービス | `__all__` シンボルの抽出 |
| `ImportStatement` 等 | 値オブジェクト群 | AST インポートノードのラップと振る舞いのカプセル化 |

### ファイルレイアウト

#### プロダクションコード

```bash
src/paladin/rule/
├── __init__.py                       # 公開 API（__all__ で管理）
├── protocol.py                       # Rule / MultiFileRule / PreparableRule Protocol
├── types.py                          # SourceFile / SourceFiles / Violation / Violations
│                                     # RuleMeta / OverrideEntry / PerFileIgnoreEntry
├── import_statement.py               # ModulePath / ImportStatement / AbsoluteFromImport
│                                     # ImportedName / SourceLocation
├── rule_set.py                       # RuleSet
├── rule_set_factory.py               # RuleSetFactory
├── package_resolver.py               # PackageResolver
├── own_package_resolver.py           # OwnPackageResolver
├── all_exports_extractor.py          # AllExportsExtractor / AllExports
├── require_all_export.py             # require-all-export
├── no_relative_import.py             # no-relative-import
├── no_local_import.py                # no-local-import
├── no_non_init_all.py                # no-non-init-all
├── no_cross_package_reexport.py      # no-cross-package-reexport
├── no_mock_usage.py                  # no-mock-usage
├── no_deep_nesting.py                # no-deep-nesting
├── no_third_party_import.py          # no-third-party-import（PreparableRule）
├── no_cross_package_import.py        # no-cross-package-import（PreparableRule）
├── require_qualified_third_party.py  # require-qualified-third-party（PreparableRule）
├── max_method_length.py              # max-method-length
├── max_class_length.py               # max-class-length
├── max_file_length.py                # max-file-length
├── no_direct_internal_import.py      # no-direct-internal-import（MultiFileRule + PreparableRule）
├── no_unused_export.py               # no-unused-export（MultiFileRule + PreparableRule）
└── no_testing_test_code.py           # no-testing-test-code（MultiFileRule）
```

#### テストコード

```bash
tests/unit/test_rule/
├── __init__.py
├── helpers.py
├── test_all_exports_extractor.py
├── test_import_statement.py
├── test_max_class_length.py
├── test_max_file_length.py
├── test_max_method_length.py
├── test_no_cross_package_import.py
├── test_no_cross_package_reexport.py
├── test_no_deep_nesting.py
├── test_no_direct_internal_import.py
├── test_no_local_import.py
├── test_no_mock_usage.py
├── test_no_non_init_all.py
├── test_no_relative_import.py
├── test_no_testing_test_code.py
├── test_no_third_party_import.py
├── test_no_unused_export.py
├── test_own_package_resolver.py
├── test_package_resolver.py
├── test_require_all_export.py
├── test_require_qualified_third_party.py
├── test_rule_set.py
├── test_rule_set_factory.py
└── test_types.py
tests/fake/
└── rule.py                           # FakeRule（テスト用フェイク実装）
```

## 処理フロー

1. `RuleSetFactory.create()` でルール一式と設定値を組み立て `RuleSet` を生成する
2. `RuleSet.run()` が `PreparableRule` 実装ルールに対して事前準備を実行する
3. 各ソースファイルに対して単一ファイルルールを適用する（無効化 ID を参照してスキップ）
4. `MultiFileRule` を全ファイルを対象に実行する
5. 収集した違反を `Violations` にまとめて返す

## 固有の設計判断

### Rule と MultiFileRule の分離

**設計の意図**: ルール実行モデルを「単一ファイル」と「複数ファイル」に明示的に分離する。`Rule` は `check(source_file)` を、`MultiFileRule` は `check(source_files)` を持つ別の Protocol として定義する。

**なぜそう設計したか**: 1つの Protocol に統一して引数を使い分ける案は、型の表現力が下がり呼び出し側が引数の型を意識する必要が生じる。`check()` を常に `SourceFiles` で受け取る案は、単一ファイルルールがファイルループを自前で行う必要があり責務が分散する。

**トレードオフ**: Protocol が2つに増えるが、型安全性とルール実装の明確化を優先した。

### PreparableRule による事前準備フェーズ

**設計の意図**: 全ファイルの情報を先に集約してから各ファイルを検査する必要があるルール（パッケージ解決など）のために、単一ファイルループの前に準備を完了できる仕組みを設ける。

**なぜそう設計したか**: `MultiFileRule` に統合する案は、単一ファイルループの外で事前集計しキャッシュする用途に不向きで実行フローが複雑になる。コンストラクタで `source_files` を受け取る案は、`RuleSetFactory` の責務が肥大化し毎回新規インスタンスが必要になる。

**トレードオフ**: Protocol が1つ増えるが、準備が不要なルールへの影響をゼロにできる。`prepare()` 呼び出し前の `check()` 呼び出しは無効な状態を返すことに注意が必要。

### Protocol による抽象化（継承回避）

**設計の意図**: ルール具象クラスが基底クラスを継承する設計を避け、`@runtime_checkable` な Protocol による構造的部分型を採用する。

**なぜそう設計したか**: 抽象基底クラス（ABC）による継承では基底クラス変更時の影響範囲が広がる。Protocol を採用することで、新規ルール追加時に独立したルールクラスを定義するだけで追加できる。

**トレードオフ**: Protocol のメソッドシグネチャ変更時に、コンパイル時ではなく実行時に検出されるケースがある。

### PackageResolver と OwnPackageResolver の分離

**設計の意図**: ファイルパスからパッケージキーを解決するロジックと、テストファイルに対応するプロダクションパッケージの同一視ロジックを分離する。

**なぜそう設計したか**: `PackageResolver` は `src/` レイアウトと `tests/` を考慮したパッケージ解決のみを担い、`OwnPackageResolver` はテストファイルのディレクトリ名（`test_view/` → `paladin.view`）からの対応プロダクションパッケージ導出を担う。クロスパッケージインポート系ルールと内部インポートルールで共通の判定ロジックを再利用できる。

**トレードオフ**: テスト固有の変換ロジックを分離することで `PackageResolver` の責務が明確化される反面、パッケージ解決の全体像を把握するには2つのクラスを理解する必要がある。

### ルールオプションのコンストラクタ経由注入

**設計の意図**: 可変オプション（`allow-dirs`・`max-lines` 等）をルールのコンストラクタで受け取り、`RuleSetFactory.create()` が設定値の解析と注入を一元化する。

**なぜそう設計したか**: 設定解析をルール内に持つ案ではルールと設定フォーマットが密結合になり、設定スキーマ変更時の影響が広がる。

**トレードオフ**: ルールクラスを純粋なドメインロジックに集中させられるが、新しいオプションを追加する際は `RuleSetFactory` の変更が必要になる。

### RuleMeta による違反生成の一元化

**設計の意図**: 違反生成をルールメタ情報と結びつけることで、各ルールが `rule_id` / `rule_name` を繰り返し参照しなくて済むようにする。`RuleMeta` に `create_violation_at()` を持たせ、`Violation` を生成する責務を与える。

**なぜそう設計したか**: ルール ID・ルール名を各違反生成コードに重複記述することを防ぎ、`RuleMeta` を起点に `Violation` が生成される流れを明確化できる。

**トレードオフ**: `RuleMeta` が値オブジェクトでありながらファクトリメソッドを持つため、純粋なデータホルダーとしての役割を超える。

## 制約と注意点

### src レイアウト前提

`PackageResolver` は `src/` ディレクトリをアンカーとしてパッケージセグメントを決定する。`src/` を使わないフラットレイアウトでは `NON_PACKAGE_DIRS` のフォールバック処理が使われるが、主要ユースケースは `src/` 配置を前提とする。

### MultiFileRule の per-file 無効化非対応

`RuleSet.run()` の `per_file_disabled` は単一ファイルルールにのみ適用される。`MultiFileRule` の無効化はグローバルな `disabled_rule_ids` のみで制御される。

### パッケージキーの先頭2セグメント制約

`resolve_package_key()` は常に先頭2セグメント（例: `paladin.check`）を返す。3階層以上のネストしたパッケージ（`paladin.foundation.model` 等）を区別する場合は `resolve_exact_package_path()` を使う必要がある。

### 副作用

- `NoDirectInternalImportRule` はサブパッケージ存在確認のために実行時にファイルシステムを参照する

上記以外のルール・ドメインサービスはすべて純粋計算であり副作用を持たない。

## 外部依存

### 外部システムへの依存

- Python 標準ライブラリの `ast` モジュールによる AST 解析
- `sys.stdlib_module_names` による標準ライブラリ判定
- ファイルシステム参照（`NoDirectInternalImportRule` のサブパッケージ検出のみ）

### サードパーティライブラリへの依存

サードパーティライブラリへの依存はない。

## 関連ドキュメント

- [rule モジュール要件定義](./requirements.md): rule モジュールの機能要件や前提条件
- [Python アーキテクチャ設計](../../design/architecture.md): プロジェクト共通の設計思想
