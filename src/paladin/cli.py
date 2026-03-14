#!/usr/bin/env python3
"""CLIツールのエントリーポイント

uv run コマンド経由での実行を想定している。
サブコマンドの実装には Typer を使い、一貫性のある体験を提供する。
各サブコマンドを定義しているメソッドでは、次の処理を実行する。

- Config から環境設定を取得し、 Context へ実行時の動的パラメータをセット
- OrchestratorProviderで静的な依存グラフを解決し、Orchestrator をインスタンス化
- Orchestrator がサブコマンドのビジネスロジックを実行

本ファイルにはビジネスロジックは持たせない。
依存するコンポーネントを適切に組み立て、Orchestrator を実行することが責務である。
なおエラー発生時は main 関数内の ErrorHandler が例外を補足し、エラーハンドリングを実行する。

Docs:
    - docs/specs/cli/requirements.md
    - docs/specs/cli/design.md

Usage:
    uv run paladin transform xxxx.md
    uv run paladin --help
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from paladin.check import CheckContext, CheckOrchestratorProvider, OutputFormat
from paladin.config import AppConfig, EnvVarConfig
from paladin.config.env_var import LogLevel
from paladin.foundation.error import ErrorHandler
from paladin.foundation.log import LogConfigurator, log
from paladin.rules import RulesContext, RulesOrchestratorProvider
from paladin.transform import TransformContext, TransformOrchestratorProvider
from paladin.version import VersionOrchestratorProvider

logger = logging.getLogger(__name__)
app = typer.Typer(no_args_is_help=True)


@app.command()
def check(
    ctx: typer.Context,
    targets: Annotated[list[Path], typer.Argument(help="解析対象のファイルまたはディレクトリ")],
    format: Annotated[OutputFormat, typer.Option("--format", help="出力形式")] = OutputFormat.TEXT,
    ignore_rule: Annotated[
        list[str] | None, typer.Option("--ignore-rule", help="無視するルール ID（複数回指定可）")
    ] = None,
) -> None:
    """解析対象の .py ファイルを診断し、違反レポートを出力する"""
    context = CheckContext(
        targets=tuple(targets),
        format=format,
        ignore_rules=frozenset(ignore_rule or []),
    )
    report = CheckOrchestratorProvider().provide().orchestrate(context)
    typer.echo(report.text)
    raise typer.Exit(code=report.exit_code)


@app.command()
def rules(
    rule: Annotated[str | None, typer.Option("--rule", help="特定ルールの詳細を表示")] = None,
) -> None:
    """利用可能なルールの一覧を表示する"""
    context = RulesContext(rule_id=rule)
    text = RulesOrchestratorProvider().provide().orchestrate(context)
    typer.echo(text)


@app.command()
def version() -> None:
    """パッケージのバージョン文字列を表示する"""
    text = VersionOrchestratorProvider().provide().orchestrate()
    typer.echo(text)


@app.command()
def transform(
    ctx: typer.Context,
    target_file: Annotated[Path, typer.Argument(help="ファイルパス")],
    tmp_dir: Annotated[
        Path | None,
        typer.Option("--tmp-dir", help="一時ディレクトリパス"),
    ] = None,
) -> None:
    """テキストファイルを読み込み、行番号を付与して出力"""
    config = _get_config(ctx)
    context = TransformContext(
        target_file=target_file,
        tmp_dir=tmp_dir if tmp_dir is not None else config.tmp_dir,
        current_datetime=datetime.now(),
    )
    orchestrator = TransformOrchestratorProvider().provide()
    result = orchestrator.orchestrate(context)
    print(result.to_json())


@log
def _get_config(ctx: typer.Context) -> AppConfig:
    """Typer ContextからAppConfigを取得

    @app.callback() でセットした値を取得する。
    Typer依存のコードを分散させないため、プライベートメソッドとしてカプセル化する。
    """
    return ctx.obj


@app.callback()
def main_callback(
    ctx: typer.Context,
    log_level: Annotated[
        LogLevel | None,
        typer.Option("--log-level", help="ログレベル (CRITICAL/ERROR/WARNING/INFO/DEBUG)"),
    ] = None,
) -> None:
    """各サブコマンドの事前処理"""
    config = AppConfig.build(env=EnvVarConfig(), log_level=log_level)
    _initialize_logger(config.log_level, ctx.invoked_subcommand)
    _setup_context(ctx, config)


def _initialize_logger(log_level: LogLevel, app_name: str | None) -> None:
    """ロガーの初期化

    本アプリケーションではプレーンテキスト形式でログを出力する。
    """
    log_configurator = LogConfigurator(level=log_level, app_name=app_name)
    log_path = log_configurator.configure_plain()
    logger.info("Started %s command", app_name)
    logger.info("Log file: %s", log_path)


@log
def _setup_context(ctx: typer.Context, config: AppConfig) -> None:
    """Typer Contextのセットアップ

    グローバルオプションや環境変数から取得した値を、
    Typer Context経由でサブコマンドへ渡せるようにする。
    """
    ctx.ensure_object(dict)
    ctx.obj = config


def main() -> None:
    """メイン関数"""
    try:
        app()
    except Exception as e:
        ErrorHandler().handle(e)
        sys.exit(2)


if __name__ == "__main__":
    main()
