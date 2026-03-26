---
name: python-review
description: Use when reviewing Python code for comment quality and testing practices, running code review after implementation, or checking code changes before merging. Supports Python code review to deliver review findings and automatic fixes.
argument-hint: "[target (optional)]"
disable-model-invocation: false
user-invocable: true
model: inherit
---

# Python Code Review

Python コードを複数のレビュー観点から並列にレビューし、結果を集約して自動修正する。

## Context

### User input

<target> $ARGUMENTS </target>

## Reviewer Registry

| Name | Agent File | Scope | Description |
|------|-----------|-------|-------------|
| comment-reviewer | agents/comment-reviewer.md | production | docstring/コメントの品質チェック |
| testing-reviewer | agents/testing-reviewer.md | test | テスト設計ルールのチェック |

Scope:
- production: src/ 配下
- test: tests/ 配下
- all: 全ファイル

## Instructions

### Step 1: 対象ファイルの収集

<target> の内容に基づき対象ファイルを収集する。

- 引数あり（ファイル）: そのファイルを対象に追加
- 引数あり（ディレクトリ）: Glob で `{ディレクトリ}/**/*.py` を再帰検出
- 引数なし: `git diff main --name-only --diff-filter=ACMR -- src/ tests/` で変更ファイルを取得

収集したファイルを分類する:
- production: src/ 配下の .py
- test: tests/ 配下の .py

結果が空の場合はメッセージを出力して終了。

### Step 2: レビューサブエージェントの並列起動

Reviewer Registry の各レビュアーについて:

1. Scope に基づき対象ファイルリストをフィルタ
2. 対象ファイルが 0 件のレビュアーはスキップ
3. `${CLAUDE_SKILL_DIR}/agents/{agent-file}` を Read で読み込む
4. 読み込んだ内容の `{ファイルリスト}` プレースホルダーを対象ファイルリストで置換
5. Agent ツールで general-purpose サブエージェントを起動

全レビュアーを単一メッセージで並列起動する。

### Step 3: レビュー結果の集約・提示

全サブエージェント完了後:

1. 各レビュアーの結果を集約
2. 重要度順（high → medium → low）にソート
3. ユーザーにレビュー結果サマリーを提示
4. 問題が 0 件の場合はここで終了

### Step 4: 修正サブエージェントの並列起動

レビュー結果に問題があるファイルごとに:

1. `${CLAUDE_SKILL_DIR}/agents/fix-agent.md` を Read で読み込む
2. プレースホルダーを置換:
   - `{ファイルパス}`: 修正対象ファイル
   - `{レビュー結果}`: そのファイルに関する問題一覧
3. Agent ツールで general-purpose サブエージェントを起動

全ファイルの修正サブエージェントを単一メッセージで並列起動する。

### Step 5: 最終検証

全修正完了後、Bash ツールで `make all` を実行して検証する。

`make all` が失敗した場合:

1. エラー内容を分析し、原因となった修正ファイルを特定する
2. 該当ファイルに対して fix-agent を再起動する（エラー情報をレビュー結果に追加して渡す）
3. 再修正後、再度 `make all` を実行する
4. 2回目も失敗した場合、`git checkout -- {問題ファイル}` で該当ファイルの修正をリバートし、スキップした旨をユーザーに報告する

## Constraints

- 引数指定時は確認なしに即座に処理開始
- レビュー対象は .py ファイルのみ
- レビューサブエージェントは Read のみ（修正しない）
- 修正サブエージェントはレビュー結果に記載された問題のみ修正（独自判断で追加修正しない）
- 修正完了後は `make all` で検証
- `make all` が失敗した場合は最大1回リトライし、2回目も失敗したら該当ファイルの修正をリバートする
