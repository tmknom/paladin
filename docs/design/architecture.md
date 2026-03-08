# Pythonアーキテクチャ設計

本プロジェクトのPythonコードベースにおけるアーキテクチャ設計の全体像を示す。

## 基本原則

実装判断で迷ったら最初に立ち返る原則集。

- **高凝集・疎結合**: 関連する機能を1箇所に集め、モジュール間の依存を最小化
- **KISS（Keep It Simple, Stupid）**: シンプルな設計を優先、過度な抽象化を避ける
- **DRY（Don't Repeat Yourself）**: 知識の重複を避ける（コードではなく仕様・ルール・変換規則の重複を避ける）
- **YAGNI（You Aren't Gonna Need It）**: 今必要な最小限のみを実装、将来の拡張は必要になってから
- **Fail Fast**: 失敗は早く顕在化させる、境界でバリデーション
- **明示は暗黙に勝る（Explicit is better than implicit）**: 暗黙の動作より明示的な設計を優先
- **不変と副作用の分離**: データは不変を既定に、副作用を持つ処理は明確に分離
- **抽象に依存し、境界で実装詳細を隠す**: 実装ではなく抽象（Protocol）に依存
- **名前は概念を正確に表す**: 役割・制約・単位を含め、読み手に意図を伝える

## アーキテクチャ全体像

### 設計目標

本プロジェクトでは、次の品質特性を重視して設計する:

1. **技術独立性**: 外部システム（Database、External Service等）の変更がビジネスロジックに影響しない
2. **テスタビリティ**: 外部APIやI/Oをモックに差し替えてテスト可能
3. **変更容易性**: データパイプライン、検索、質問応答の各機能を独立して進化可能
4. **可読性と保守性**: 各層の責務を明確にし、影響範囲を限定

### レイヤー構成

本プロジェクトは、明確な単方向依存を持つ2つのレイヤーと、横断的共通部品（Shared Kernel）で構成される:

```
        ┌───────────────────────┐
        │ CLI層                 │ ← 最外殻
        │  ┌─────────────────┐  │
        │  │ ビジネスロジック層│  │ ← 最内殻（中核）
        │  └─────────────────┘  │
        └───────────────────────┘
              ↑ 両層から参照
        ┌───────────────────────┐
        │ protocol              │ ← Shared Kernel（OnionのPort定義）
        └───────────────────────┘
              ↑ foundation も参照（実装のため）
        ┌───────────────────────┐
        │ foundation            │ ← Shared Kernel（横断的共通部品・Adapter実装）
        │（FS・エラー・ログ等）  │
        └───────────────────────┘
```

**重要な原則**:
- 依存は常に外側 → 内側の単方向（CLI → ビジネスロジック）。内側の層は外側の層を知らない。循環依存は禁止。
- `protocol/` は層ではなく Shared Kernel（Port定義）。OnionアーキテクチャのPort（抽象インターフェース）を定義し、ビジネスロジック層と foundation（Adapter）の両方から参照される。
- `foundation/` は層ではなく Shared Kernel（横断的共通部品）。CLI層・ビジネスロジック層の両方から参照される。

### 各層の責務

| レイヤー / 区分 | 責務 | 具体例 |
|---------|-----|--------|
| **CLI層** | コマンドライン処理、実行時コンテキスト、エラーハンドリング | Typer、main関数、ユーザー向けエラーメッセージ |
| **ビジネスロジック層** | 全体処理制御、ドメイン固有の処理 | Orchestrator、Processor、DataTransformer |
| **protocol（Shared Kernel）** | OnionアーキテクチャのPort定義（抽象インターフェース）。ビジネスロジック層とfoundation（Adapter）の境界を提供する | TextFileSystemReaderProtocol、TextFileSystemWriterProtocol |
| **foundation（Shared Kernel）** | 横断的共通部品のAdapter実装（外部システムアクセス、エラー処理、ログ、データモデル基盤）。特定の機能に属さず両層から利用される | TextFileSystemReader（Adapter）、ErrorHandler、@log |

**foundationに置けるものの判断基準**:
- 機能に依存しない、横断的で安定したAdapter実装のみ
- feature固有の概念が1つでも混ざるなら `<feature>/` に置く
- Protocolの定義（Port）は `foundation/` ではなく `protocol/` または `<feature>/` に置く
- 迷ったら `<feature>/` に置く（YAGNI）

### パッケージ構成とファイルレイアウト

`<xxx>` はプロジェクトが決める名前を示す（PJによって異なる）。

```
src/myapp/
├── <config>/                # 環境設定（CLI層が読み込む）
│   └── path.py              #   PathConfig（frozen dataclass）
├── <protocol>/              # OnionアーキテクチャのPort定義（横断的共有Protocol）
│   └── fs.py                #   TextFileSystemReaderProtocol / TextFileSystemWriterProtocol
├── <foundation>/            # 基盤パッケージ（横断的機能）
│   ├── error/               #   エラー処理（ApplicationError, ErrorHandler）
│   ├── fs/                  #   ファイルシステム
│   │   └── text.py          #     Adapter実装（TextFileSystemReader等）
│   ├── log/                 #   ロギング（@log, LogConfigurator）
│   └── model/               #   データモデル基盤（CoreModel）
├── <feature>/               # 機能パッケージ（ビジネスロジック、機能ごとに1つ）
│   ├── types.py             #   戻り値・値オブジェクト（frozen dataclass）
│   ├── context.py           #   実行時コンテキスト（frozen dataclass）
│   ├── reader.py            #   薄いラッパー（Protocol呼び出しと入出力の型合わせのみ）
│   ├── writer.py            #   薄いラッパー（Protocol呼び出しと入出力の型合わせのみ）
│   ├── transformer.py       #   純粋計算モジュール（副作用なし、Protocol不要）※任意
│   ├── orchestrator.py      #   Orchestrator
│   └── provider.py          #   Composition Root
└── cli.py                   # CLI層（エントリーポイント）
```

**各パッケージに置くべきもの**:

| パッケージ | 置くもの | 置かないもの |
|----------|--------|------------|
| `<protocol>/` | OnionのPort定義（複数機能から共有されるProtocol）（例: `TextFileSystemReaderProtocol`） | 機能固有のProtocol、Adapter実装 |
| `<foundation>/error/` | ApplicationError基底クラス、ErrorHandler | 機能固有のXxxError、ビジネスロジック固有のバリデーション |
| `<foundation>/fs/` | Adapter実装のみ | Protocolの定義（それは `<protocol>/` または `<feature>/` に置く） |
| `<foundation>/log/` | @logデコレータ、LogConfigurator | アプリケーション固有のログフォーマット |
| `<foundation>/model/` | CoreModel（Pydantic基底クラス） | ビジネスロジック固有のモデル |
| `<feature>/` | Context、Result、薄いラッパー、純粋計算モジュール（任意）、Orchestrator、Provider | 外部ライブラリへの直接依存、ドメイン変換（正規化・集約・検証ルールはOrchestrator/Processorへ） |
| `<config>/` | 環境設定クラス（PathConfig等） | ビジネスロジック固有の設定 |

### パターンの協調構造

各パターンは独立したものではなく、役割分担によって協調する。

```
┌─────────────────────────────────────────────────────┐
│ CLI層                                               │
│  XxxConfig            ← 環境設定（config/）         │
│  XxxContext           ← Context パターン            │
│  XxxOrchestratorProvider ← Composition Root       │
└───────────────────────────┬─────────────────────────┘
                            │ orchestrate(context)
┌───────────────────────────▼─────────────────────────┐
│ ビジネスロジック層                                  │
│  XxxOrchestrator      ← Orchestrator               │
│  各種 Reader/Writer   ← Protocol型で注入受ける薄いラッパー│
└───────────────────────────┬─────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────┐
│ protocol（Shared Kernel）                           │
│  各種 Protocol        ← OnionのPort（抽象インターフェース）│
└───────────────────────────┬─────────────────────────┘
                            │ Adapter が実装（明示的継承）
┌───────────────────────────▼─────────────────────────┐
│ foundation（Shared Kernel）                         │
│  各種 Adapter         ← Protocolを継承した具象実装   │
│  （FS, 外部API, サードパーティライブラリ等）          │
│  ErrorHandler         ← 例外ログ担当               │
└─────────────────────────────────────────────────────┘
```

接続の要点:
- Provider（静的な依存グラフの構築）と Context（実行時の動的パラメータ）は役割が異なる
- 環境設定（config/）は CLI 層で読み込み、Context に組み込まれて Orchestrator に届く
- OnionのPort（ビジネスロジック側の抽象IF）は `<feature>/protocol.py`（機能固有）または `<protocol>/`（複数機能で共有）に定義する
- `<protocol>/` に定義したProtocolは、ビジネスロジック層（Reader/Writer等）とfoundation（Adapter実装）の両方から参照される
- foundation の各Adapterパッケージは Protocol を import して継承するが、export はしない（Port/Adapter 境界の維持）

### 実行時フロー

起動から完了までの制御フローと、各パターンの担当箇所:

```
main()
  ↓ 環境設定を読み込む
      [設定層] デプロイ環境依存の値を確定する

  ↓ XxxOrchestratorProvider().provide()
      [Composition Root] foundation の Adapter を組み立て、feature 側の Port（Protocol）として注入する

  ↓ XxxContext(target_file, tmp_dir=xxx_config.tmp_dir, current_datetime=datetime.now())
      [Context パターン] 実行時パラメータを不変オブジェクトに封じ込める
      ※ XxxConfig の値はここで Context に取り込まれ、Orchestrator には直接渡らない

  ↓ orchestrator.orchestrate(context)
      [Orchestrator] Context のみに依存して処理を実行
      └ reader.read(...)
      └ 変換処理（純粋な計算: Protocol 不要）
      └ writer.write(...)
      └ return XxxResult(...)

  except Exception as e:
      基盤層に委譲し、CLI 層が終了コードを決定する
```

## Protocol: コードベースの健全性を保つ中核メカニズム

Protocol はコードベース全体の健全性を守るための積極的な設計メカニズムである。「実装詳細を隠す技術的手段」ではなく、テスタビリティの確保とライブラリ依存の封じ込めを目的とする。純粋な計算処理には不要であり、以下の2つの目的に該当する処理にのみ適用する。

### 目的1: 副作用の分離

副作用（ファイルI/O・DBアクセス・外部API・通知/キューへのリクエストなど）を持つ処理を Protocol で抽象化する。

**なぜ分離するか**: テスト時にモック/スタブに差し替えることでテスタビリティを確保する。実際のネットワーク通信やディスクアクセスなしにユニットテストを実行できる。

**適用できる例**（アプリケーションの種類に応じて選択する）:

| 副作用の種類 | 具体例 |
|------------|--------|
| ファイルI/O | `TextFileSystemReaderProtocol` |
| DBアクセス | `UserRepositoryProtocol` |
| 外部APIリクエスト | `ExternalServiceClientProtocol` |
| 通知/キュー | `NotificationClientProtocol` |

### 目的2: サードパーティの隔離

外部ライブラリのインターフェースがビジネスロジック層に直接漏れると、ライブラリのアップデートや乗り換え時にコードベース全体が影響を受ける。Protocol を挟むことで、影響範囲を基盤層のAdapter実装のみに局所化できる。

（例: HTTPクライアントを `requests` から `httpx` に替えても Orchestrator のコードは変わらない）

なお、副作用とサードパーティ依存は多くの場合重複する（外部APIはどちらにも該当する）。
判断の出発点は「テスト時に差し替えたいか」「ライブラリ依存をビジネスロジック層に持ち込みたくないか」。

### Protocol適用の判断基準

| 目的 | 対象 | 具体例 |
|------|------|--------|
| **副作用の分離** | テスト時に差し替えが必要な処理 | ファイルI/O、DB、時刻取得、乱数生成 |
| **サードパーティの隔離** | 外部ライブラリへの直接依存を避けたい処理 | 外部APIクライアント（HTTPクライアント等）、ORMラッパー、暗号化ライブラリ |

### Structural Subtyping（構造的部分型）

実装クラスがProtocolに明示的に継承しなくても、メソッドシグネチャが一致していれば準拠できる。これにより、既存クラスを変更せずにProtocolに適合させることが可能になる。

### Protocolの配置ルール

Protocolの配置場所は、そのProtocolが参照される範囲によって決まる:

| 配置場所 | 対象 | 具体例 |
|---------|------|--------|
| `<protocol>/` | 複数のfeatureまたはfoundationから共有されるProtocol | `TextFileSystemReaderProtocol`（transform と foundation/fs の両方が参照） |
| `<feature>/protocol.py` | 特定のfeature固有のProtocol | そのfeatureパッケージ内のみで使用するProtocol |

**Providerが担う役割**:
Providerは `foundation/` の具象クラス（Adapter）を組み立てて、`protocol/` で定義されたProtocol型としてOrchestratorに注入する唯一の場所。
ビジネスロジック層は具象クラス（foundation の Adapter）を直接参照しない。

## Composition Root + Orchestrator パターン

各機能は、依存性注入と処理制御を分離した共通パターンで構成される:

```
Provider (Composition Root)
    ↓ オブジェクトグラフを生成
Orchestrator
    ↓ 処理フローを制御
各種コンポーネント
```

**役割分担**:
- **Provider (Composition Root)**: アプリケーションのエントリーポイント近くで、必要な依存関係（Database、External Service等のクライアント）をまとめて初期化し、Orchestratorに注入
- **Orchestrator**: ビジネスロジックの処理フロー全体を制御。各処理コンポーネントを順次実行

**なぜこのパターンを採用したか**:
- **Composition Rootパターン**: エントリーポイント近くで依存関係を一箇所にまとめることで、依存性注入を明示的に管理（書籍「DIの原理・原則とパターン」で推奨されるパターン）
- **Orchestrator抽象化**: ビジネスロジックをエントリーポイント（CLI、REST API等）から独立させることで、インターフェース変更時もビジネスロジック層は不変

## Orchestrator-Processorパターン（複数API vs 単一API）

**単一フローの処理（1エンティティを1回処理）では Orchestrator のみで十分。**
複数のエンティティ（API、データ等）を一括処理する場合に限り、**Orchestrator（イテレーション管理）**と**Processor（単一エンティティ処理）**に責務を分離します:

```
Orchestrator
    ↓ エンティティ一覧の取得
    ↓ for entity in entities:
    └→ Processor.process(entity)
           ↓ 単一エンティティの処理
           ↓ データ読み込み・変換・生成
           └→ 結果保存
```

**役割分担**:

| コンポーネント | 責務 | 具体例 |
|-------------|------|--------|
| **Orchestrator** | ・エンティティ一覧の取得<br>・`for entity in entities:` イテレーション<br>・結果の集約<br>・CLIからの独立 | `orchestrate(targets: tuple[str, ...])` |
| **Processor** | ・単一エンティティの処理ロジック<br>・データ読み込み・変換・生成<br>・ファイル保存 | `process(api: Api)` |

**なぜこのパターンを採用したか**:
- **テスタビリティ**: Processorを個別にテスト可能。モックAPIを使い、単一API処理とイテレーション制御を独立してテストできる
- **保守性**: 単一エンティティ処理の変更がProcessorに局所化され、影響範囲が限定される。バグ修正や機能追加がしやすい

## Onion Architecture（オニオンアーキテクチャ）

Onion Architecture は、Protocol を活用した代表的なアーキテクチャパターンである。外部システム（Database、External Service、ファイルシステム等）への依存を抽象化し、ビジネスロジックを外部変化から保護する。

```
ビジネスロジック層（transform/）
    ↓ Protocol（Port）経由で依存  ← example.protocol を import
protocol/（Port定義）
    ↑ 実装（明示的継承）
foundation/（Adapter：具象実装）
    ↓ 実際の通信
外部システム（DB、FS、外部API等）
```

Pythonではこの Port/Adapter の境界を `Protocol` で実装する。
`protocol/` パッケージが Port の定義場所であり、ビジネスロジック層は `protocol/` のみに依存し、foundation の具象クラスを直接参照しない。
Provider（Composition Root）のみが foundation の具象クラス（Adapter）を参照し、Protocol 型として組み立てる。

## 型設計（ドメインモデルとマッピング）

本プロジェクトでは、用途に応じて3種類の型を使い分ける:

### 型の使い分け

| 用途 | 使用する型 | 理由 |
|------|-----------|------|
| 外部データ（JSON/YAML） | **CoreModel (Pydantic)** | バリデーション必須、外部データの隔離 |
| 処理結果・値オブジェクト | **dataclass** | シンプルで軽量、不変性の保証 |
| 意味的制約の付与 | **NewType** | 型安全性向上、実行時オーバーヘッドなし |

### 各型の役割

**CoreModel（Pydantic）**:
- 外部システム（API、ファイル）から取得したJSON/YAMLデータをマッピング
- 境界（基盤層）でバリデーションを実施し、不正データを早期検出
- `frozen=True`で不変性、`extra="forbid"`で未知フィールド拒否がデフォルト

**dataclass**:
- 実行時コンテキスト（例: `ExtractContext`、`SearchContext`）
- 処理結果（例: `ExtractResult`、`SearchResult`）
- バリデーション不要な内部データ構造

**NewType**:
- 同じ基底型でも役割が異なることを明示（例: `InputFilePath`, `OutputDirPath`）
- 関数シグネチャの可読性向上
- 静的型チェックのみで実行時オーバーヘッドなし

### 型定義分離の実用的な効果

型定義を独立したファイル（`types.py`）に分離することで、以下の効果が得られる:

- **型定義の安定性**: 実装クラスの変更が型定義に影響しない
- **再利用性**: 複数のモジュールから同一の型を参照可能
- **循環依存の回避**: 相互参照するモジュール間での循環インポートを防止

## 設定の分離と配置原則

設定情報をスコープと変更理由に基づいて2分類する:

| 種別 | スコープ | 配置場所 | 例 |
|------|--------|---------|-----|
| **環境設定** | 横断的（全機能共通） | `src/myapp/config/` | PathConfig、ServiceConfig |
| **パッケージ固有設定** | パッケージ単位 | `src/myapp/<feature>/` | FooPackageConfig（top_k等） |

環境設定はデプロイ環境（開発/本番）で値が変わり、アプリ起動時に確定する。
パッケージ固有設定はそのパッケージの振る舞いを制御し、精度・性能チューニングに使う。

### Providerとの接続

設定の2分類は、Provider と Context の設計に直接マッピングされる。

| 設定種別 | 読み込みタイミング | 受け渡し先 | 対応パターン |
|---------|-----------------|-----------|-------------|
| 環境設定 | main() 起動時 | Context のフィールドとして組み込む | Context パターン |
| パッケージ固有設定 | Provider 初期化時 | Orchestrator に注入 | Composition Root |

## 実行時コンテキストのカプセル化（Context パターン）

実行時に決まる値（CLIの引数、ファイルパス、現在日時など）を1つの値オブジェクト（Context）にカプセル化し、CLI層で組み立ててから Orchestrator に渡す:

```
CLI層（main / コマンド関数）
    ↓ PathConfig・引数・datetime.now() を収集
Context オブジェクトを組み立て（frozen dataclass）
    ↓ orchestrate(context) で渡す
Orchestrator
    ↓ context.xxx を参照して処理
Result を返す
```

**役割分担**:

| コンポーネント | 責務 | 具体例 |
|--------------|------|--------|
| **CLI層** | 実行時の値を収集し Context を組み立てる | `TransformContext(target_file=..., current_datetime=datetime.now())` |
| **Context**（値オブジェクト） | 処理に必要な実行時情報を不変オブジェクトとして保持 | `TransformContext`（`frozen=True` の dataclass） |
| **Orchestrator** | Context のみに依存して処理を実行。外部状態を参照しない | `orchestrate(context: TransformContext) -> TransformResult` |

**Context の構造**:
- `frozen=True` の dataclass（値オブジェクト）
- フィールド例: `target_file`（対象ファイルパス）、`tmp_dir`（出力先ディレクトリ）、`current_datetime`（実行日時）

**なぜこのパターンを採用したか**:
- **テスト容易性**: `datetime.now()` などの非決定論的な値を Context に封じ込めることで、テストでは `datetime(2026, 1, 1, ...)` のような固定値を渡せる。Orchestrator は外部状態に依存しない純粋な処理になる
- **変更頻度の分離**: CLIの引数・環境設定・実行日時はそれぞれ変更理由が異なる。Context に集約することで「どこで組み立てるか」と「どう処理するか」を分離する
- **責任の明確化**: 「Context を組み立てる責任」はCLI層（エントリーポイント）に集約される。Orchestrator は受け取った Context をそのまま使うだけでよく、値の取得方法を知らなくてよい
- **Composition Root との整合**: Provider（Composition Root）が静的な依存関係を組み立て、Context が実行時の動的な情報を担う。両者の役割が明確に分離される

## 例外ハンドリング設計（ApplicationError パターン）

例外は「発生箇所で即 raise、最上位で一括処理」を原則とし、`ApplicationError` 基底クラスと `ErrorHandler` で一貫したエラー処理を実現する。

```
各コンポーネント（Processor等）
    ↓ ApplicationError を raise（素通り）
Orchestrator / ビジネスロジック層
    ↓ 原則キャッチしない（素通り）
main()（CLI層）
    ↓ except Exception as e:
ErrorHandler().handle(e)
    ↓ ログ出力のみ（sys.exit は呼ばない）
sys.exit(1)
```

**役割分担**:

| コンポーネント | 責務 | 具体例 |
|--------------|------|--------|
| **各コンポーネント** | ApplicationError を継承した例外を raise | `StorageError`, `ValidationError` |
| **Orchestrator / ビジネスロジック層** | 原則としてキャッチしない（素通り） | `orchestrate()` に try-except を置かない |

**なぜこのパターンを採用したか**:
- **キャッチ判断の単純化**: ApplicationError か否かだけで判断できる。「キャッチしない＝素通り」が原則で、上位レイヤーが個別に try-except を書く必要がない
- **責任境界の明確化**: ErrorHandler はログ出力のみ担当し、sys.exit は呼ばない。終了判断を CLI 層（main()）に残すことで、CLI 以外（REST API 等）からも ErrorHandler を再利用できる
- **Fail Fast 原則との整合**: 設計原則の「Fail Fast」と直接対応。問題発生箇所で即座に raise し、上位へ伝播させることでエラーを隠蔽しない

## @log デコレータによる横断的ロギング

ロギングは横断的関心事（Cross-Cutting Concern）であり、ビジネスロジックに散らばりやすい。`@log` デコレータを使うことで、各メソッドにロギングコードを埋め込まずに入出力の自動記録を実現する。

```
メソッド呼び出し（@log 付き）
    ↓ INFO: 関数名・引数をログ出力
メソッド本体を実行
    ↓ 正常終了 → INFO: 戻り値をログ出力
    ↓ 例外発生 → ログなしで例外を再送出
           ↓ （ErrorHandler が例外ログを担当）
```

各メソッドへのログ出力を自分で書く代わりに `@log` を使うことで、
ビジネスロジックにログコードを混在させずコードをクリーンに保てる。

**秘匿情報に関するルール**:
- パスワード・トークン・APIキーなど秘匿情報が混入しうる引数/戻り値を扱うメソッドには `@log` を付けない（ログに秘匿情報が記録されるリスクがある）
- どうしても `@log` を付ける必要がある場合は、引数・戻り値に渡す前に必ずマスク処理を行う

**なぜこのパターンを採用したか**:
- **横断的関心事の分離**: 各メソッドにロギングコードを埋め込まず、デコレータで一元管理。メソッドの本体がビジネスロジックのみで構成される
- **ErrorHandler との役割分担**: 例外時はログせず再送出することで、ログ出力の責任を ErrorHandler に集約。「例外ログは ErrorHandler が担当する」というルールを一貫させる

## ガードレール（禁止事項と例外規定）

実装の境界を守るための明示的なルール。コードレビューの基準として使う。

### Orchestrator

| ルール | 理由 |
|-------|------|
| Context以外の外部状態を参照しない（`datetime.now()` 等を直接呼ばない） | Orchestratorが純粋関数に近づき、固定値を渡すだけでテストできる |
| Config を直接受け取らない（Contextのフィールドに含めてもらう） | 設定の取得方法をOrchestratorが知る必要はない |

### Processor

| ルール | 理由 |
|-------|------|
| イテレーションを持たない（単一エンティティのみ処理） | イテレーション制御はOrchestratorが担う。責務を明確に分離する |
| Orchestratorを参照しない | 循環依存の防止 |

### Reader / Writer

| ルール | 理由 |
|-------|------|
| 変換規則（正規化・集約・検証）を持たない | 変換ロジックはOrchestrator/Processorが担う。Reader/WriterはProtocol呼び出しと入出力の型合わせのみを行う薄いラッパーである |
| ビジネスロジックを含めない | ビジネスルールが分散するとテスト・変更時の影響範囲が広がる |

### Adapter

| ルール | 理由 |
|-------|------|
| 外部SDKの型をビジネスロジック層に漏らさない（内部型に変換してから返す） | ライブラリ乗り換え時の影響範囲をAdapterに限定 |
| 戻り値の型をProtocol定義に合わせる | AdapterはビジネスロジックのProtocol契約に従う |

### CoreModel（Pydantic）

| ルール | 理由 |
|-------|------|
| 境界（基盤層）でのみ生成する | バリデーションは外部データの入口でのみ行う（Fail Fast原則） |
| 内部処理には dataclass を使う | Pydantic依存がビジネスロジック層に広がることを防ぐ |

### 関数設計

| ルール | 理由 |
|-------|------|
| 純粋な計算と副作用（I/O、DB等）を1つの関数に混在させない | テスタビリティと可読性。純粋計算はProtocolなしで直接テスト可能 |
| 副作用を持つ処理はProtocol経由にする | テスト時にモックへの差し替えを可能にする |
| Protocol を設計する際は「副作用の分離」か「サードパーティの隔離」のいずれかの目的を明確にする | 目的なき Protocol は不要な抽象化（KISS・YAGNI 違反） |
