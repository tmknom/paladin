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
    - docs/internal/cli.md

Usage:
    uv run paladin transform xxxx.md
    uv run paladin --help
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated

# CLIエントリーポイントは typer を直接使う必要があるため、no-third-party-import を抑制する。
# typer は allow-dirs 外（src/paladin/ 直下）での利用だが、
# アプリ起動点として typer.Typer / typer.Context 等を直接参照することは設計上避けられない。
# paladin: ignore[no-third-party-import]
import typer

from paladin.check import CheckContext, CheckOrchestratorProvider
from paladin.config import AppConfig, EnvVarConfig, ProjectConfigLoader, TargetResolver
from paladin.config.env_var import LogLevel
from paladin.foundation.error import ErrorHandler
from paladin.foundation.fs import TextFileSystemReader
from paladin.foundation.log import LogConfigurator, log
from paladin.foundation.output import OutputFormat
from paladin.list import ListContext, ListOrchestratorProvider
from paladin.transform import TransformContext, TransformOrchestratorProvider
from paladin.version import VersionOrchestratorProvider
from paladin.view import ViewContext, ViewOrchestratorProvider

logger = logging.getLogger(__name__)
app = typer.Typer(no_args_is_help=True)


@app.command()
def check(
    ctx: typer.Context,
    targets: Annotated[
        list[Path] | None, typer.Argument(help="解析対象のファイルまたはディレクトリ")
    ] = None,
    format: Annotated[OutputFormat, typer.Option("--format", help="出力形式")] = OutputFormat.TEXT,
    rule: Annotated[
        list[str] | None, typer.Option("--rule", help="適用するルール ID（複数回指定可）")
    ] = None,
    ignore_rule: Annotated[
        list[str] | None, typer.Option("--ignore-rule", help="無視するルール ID（複数回指定可）")
    ] = None,
) -> None:
    """解析対象の .py ファイルを診断し、違反レポートを出力する"""
    project_config = ProjectConfigLoader(reader=TextFileSystemReader()).load()
    resolved_targets = TargetResolver().resolve(
        targets=tuple(targets) if targets else (),
        include=project_config.include,
    )
    context = CheckContext(
        targets=resolved_targets,
        format=format,
        select_rules=frozenset(rule or []),
        ignore_rules=frozenset(ignore_rule or []),
        exclude=project_config.exclude,
        rules=project_config.rules,
        per_file_ignores=project_config.per_file_ignores,
        overrides=project_config.overrides,
    )
    orchestrator = CheckOrchestratorProvider().provide(rule_options=project_config.rule_options)
    result = orchestrator.orchestrate(context)
    typer.echo(result.text)
    raise typer.Exit(code=result.exit_code)


@app.command(name="list")
def list_rules(
    format: Annotated[OutputFormat, typer.Option("--format", help="出力形式")] = OutputFormat.TEXT,
) -> None:
    """利用可能なルールの一覧を表示する"""
    context = ListContext(format=format)
    orchestrator = ListOrchestratorProvider().provide()
    result = orchestrator.orchestrate(context)
    typer.echo(result)


@app.command()
def view(
    rule_id: Annotated[str, typer.Argument(help="詳細を表示するルール ID")],
    format: Annotated[OutputFormat, typer.Option("--format", help="出力形式")] = OutputFormat.TEXT,
) -> None:
    """指定されたルールの詳細を表示する"""
    context = ViewContext(rule_id=rule_id, format=format)
    orchestrator = ViewOrchestratorProvider().provide()
    result = orchestrator.orchestrate(context)
    typer.echo(result)


@app.command()
def version() -> None:
    """パッケージのバージョン文字列を表示する"""
    orchestrator = VersionOrchestratorProvider().provide()
    result = orchestrator.orchestrate()
    typer.echo(result)


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
