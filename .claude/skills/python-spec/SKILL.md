---
name: python-spec
description: Use when documenting existing Python modules, creating specs for implemented code, or synchronizing specs with implementation changes. Supports Python specification generation to deliver accurate requirements and design documents.
argument-hint: "[module-path]"
context: fork
agent: general-purpose
disable-model-invocation: false
user-invocable: true
model: inherit
---

Python アプリケーションの実装済みモジュールから仕様ドキュメント（要件定義書・基本設計書）を自動生成する。実装コードを分析し、将来の変更時に役立つ仕様ドキュメントを作成・修正する。

## Context

Automatically embedded on skill invocation:

### Parsed arguments

!`~/.claude/skills/python-spec/scripts/parse-arguments.sh "$ARGUMENTS[0]"`

JSON fields available for use in Instructions:
- `module_path`: Input module directory path
- `module_name`: Module name (module_path with `src/<project>/` prefix removed, e.g. `src/app/foundation/fs` → `foundation/fs`)
- `requirements_path`: Output path for requirements.md
- `design_path`: Output path for design.md
- `requirements_mode`: "create" or "modify"
- `design_mode`: "create" or "modify"

## Instructions

### Step 1: ソースコードの読み込みと分析

`module_path` 配下の Python ソースコードを Glob で探索し、Read で読み込む。

`requirements_mode` または `design_mode` が `modify` の場合、該当する既存ドキュメントも Read で読み込む。

分析の観点:
- モジュールの責務と全体像
- 主要なクラス・関数の役割
- レイヤー構造とコンポーネント関係
- 外部依存関係
- データフローと処理フロー
- 設計上の重要な判断ポイント

### Step 2: 要件定義書の作成・修正

`${CLAUDE_SKILL_DIR}/references/requirements-guide.md` を Read で読み込み、ガイドラインを確認する。

#### `requirements_mode` が `create` の場合

1. ガイドラインの推奨構成に従って、要件定義書の骨格を作成
2. Step 1 の分析結果から、モジュールの目的・機能・品質要件を抽出
3. 技術実装から分離した記述（WHAT/WHY中心）で要件を記述
4. Write ツールで `requirements_path` に出力

#### `requirements_mode` が `modify` の場合

1. 既存ファイルの構成を維持しながら、実装との差分を反映
2. 既存の内容と矛盾しないよう、追加・修正を実施
3. Edit ツールで該当箇所を修正

#### 品質チェック

ガイドラインのチェックリストに従って確認:
- 内部実装詳細（クラス名・関数名・アルゴリズム）が含まれていないこと
- ユーザー向け契約仕様（CLI フラグ・設定構文・コメントディレクティブ・環境変数名・出力フォーマット）は含めてよい
- 「何ができるか」で記述されていること
- 設計詳細（HOW）が混入していないこと

問題がある場合は自動修正を実施する。

### Step 3: 設計書の作成・修正

`${CLAUDE_SKILL_DIR}/references/design-guide.md` を Read で読み込み、ガイドラインを確認する。

#### `design_mode` が `create` の場合

1. ガイドラインの推奨構成に基づいて構造を作成
2. Step 1 の分析結果から、アーキテクチャ・設計判断・処理フローを抽出
3. 設計判断の根拠を明示する記述（HOW + なぜそう設計したか）で記述
4. Mermaid を活用してコンポーネント関係・処理フローを視覚化（ファイルレイアウトは bash コードブロック）
5. Write ツールで `design_path` に出力

#### `design_mode` が `modify` の場合

1. 既存ファイルの構造を維持しつつ、実装との差分を反映
2. ガイドラインに沿っていない部分があれば改善
3. Edit ツールで該当箇所を修正

#### 品質チェック

ガイドラインのチェックリストに従って確認:
- 設計判断の根拠が明記されているか
- Mermaid 図でコンポーネント関係・処理フローが視覚化されているか
- 変更パターン別ガイドと影響範囲が記述されているか
- 要件定義（WHAT/WHYのみ）の記述が混入していないか

問題がある場合は自動修正を実施する。

### Step 4: 整合性チェック

Step 2 と Step 3 で作成・修正した両ドキュメントを Read で読み込み、以下を検証する。

**責務の逸脱チェック:**

1. **requirements.md の責務チェック**:
   - 設計詳細（HOW）が混入していないか
   - 内部実装詳細（クラス構造・アルゴリズム・処理フロー）が含まれていないか
   - ユーザー向け契約仕様（CLI フラグ・設定構文・コメントディレクティブ）は含まれていてよい
   - 「どう実装するか」ではなく「何ができるか」で記述されているか

2. **design.md の責務チェック**:
   - 要件定義（WHAT/WHYのみ）の記述が混入していないか
   - 設計判断の根拠なしに機能要件を列挙していないか
   - 「何を実現するか」だけの記述になっているセクションがないか

**ドキュメント間の整合性チェック:**

3. **矛盾の検出**:
   - requirements.md と design.md で矛盾する記述がないか
   - 用語や概念が統一されているか
   - requirements.md で定義された機能が design.md で漏れなくカバーされているか

問題を検出した場合は Edit ツールで修正し、修正内容をサマリーとして報告する。

### Step 5: 完了報告

作成・修正したドキュメントのパスを報告する:

```
Created/Updated specification documents:
- requirements_path
- design_path
```

## Constraints

- 実装コードのコピー禁止。仕様ドキュメントには将来の変更時に役立つ情報のみを記載
- モジュールの責務や全体像、設計のポイントを中心に記述
- 要件定義は技術実装から分離した記述（WHAT/WHY中心）
- 設計書は設計判断の根拠を明示（HOW + なぜそう設計したか）
- ドキュメント全体（requirements.md と design.md）の整合性を確保
- 歴史的経緯や、特定のコミットハッシュ・PR番号に言及しない
- 推測による補完をしない（実装に記載のない内容は補完しない）
- エラー発生時はサマリーをユーザーへ提示
- 仕様書の言語: 日本語（ファイルパス、コード例、技術用語は英語）
