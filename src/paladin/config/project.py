"""Configパッケージのプロジェクト設定読み込みモジュール

pyproject.toml を情報源とする。
"""

import logging
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from paladin.foundation.fs import FileSystemError
from paladin.protocol import TextFileSystemReaderProtocol
from paladin.rule import OverrideEntry, PerFileIgnoreEntry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProjectConfig:
    """プロジェクト設定を保持する値オブジェクト"""

    project_name: str | None = field(default=None)
    per_file_ignores: tuple[PerFileIgnoreEntry, ...] = field(default=())
    rules: dict[str, bool] = field(default_factory=lambda: {})
    include: tuple[str, ...] = field(default=())
    exclude: tuple[str, ...] = field(default=())
    overrides: tuple[OverrideEntry, ...] = field(default=())
    rule_options: dict[str, dict[str, object]] = field(default_factory=lambda: {})


class ProjectConfigLoader:
    """pyproject.toml からプロジェクト設定を読み込むローダー"""

    def __init__(self, reader: TextFileSystemReaderProtocol) -> None:
        """依存オブジェクトを受け取り初期化する。"""
        self._reader = reader

    def load(self) -> ProjectConfig:
        """pyproject.toml を読み込み ProjectConfig を返す

        Returns:
            ProjectConfig。ファイルが存在しない場合やセクションがない場合はデフォルト値を返す

        Flow:
            1. pyproject.toml を読み込み（失敗時はデフォルト値返却）
            2. 各セクションを個別にパース
            3. ProjectConfig を組み立てて返す
        """
        try:
            content = self._reader.read(Path("pyproject.toml"))
        except FileSystemError:
            return ProjectConfig()

        data = tomllib.loads(content)
        project_name = self._parse_project_name(data)
        per_file_ignores = self._parse_per_file_ignores(data)
        rules = self._parse_rules(data)
        include, exclude = self._parse_include_exclude(data)
        overrides = self._parse_overrides(data)
        rule_options = self._parse_rule_options(data)
        return ProjectConfig(
            project_name=project_name,
            per_file_ignores=per_file_ignores,
            rules=rules,
            include=include,
            exclude=exclude,
            overrides=overrides,
            rule_options=rule_options,
        )

    def _parse_project_name(self, data: dict[str, object]) -> str | None:
        """TOML データから [project] name をパースして正規化する

        Args:
            data: tomllib.loads() で解析した TOML データ

        Returns:
            正規化されたプロジェクト名。セクションまたは name が存在しない場合は None

        Constraints:
            正規化: 区切り文字 (-, _, .) を _ に統一し小文字に変換 (PEP 503 準拠)
        """
        try:
            project_section: dict[str, object] = data["project"]  # type: ignore[assignment]
            name: str = project_section["name"]  # type: ignore[assignment]
        except KeyError:
            return None
        return re.sub(r"[-_.]+", "_", name).lower()

    def _parse_include_exclude(
        self, data: dict[str, object]
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """TOML データから include / exclude をパースする

        Args:
            data: tomllib.loads() で解析した TOML データ

        Returns:
            (include, exclude) のタプル。キーが存在しない場合は空タプルを返す
        """
        try:
            tool_section: dict[str, object] = data["tool"]  # type: ignore[assignment]
            paladin_section: dict[str, object] = tool_section["paladin"]  # type: ignore[assignment,index]
        except KeyError:
            return (), ()

        include_raw: list[str] = paladin_section.get("include", [])  # type: ignore[assignment]
        exclude_raw: list[str] = paladin_section.get("exclude", [])  # type: ignore[assignment]
        return tuple(include_raw), tuple(exclude_raw)

    def _parse_rules(self, data: dict[str, object]) -> dict[str, bool]:
        """TOML データから rules セクションをパースする

        Args:
            data: tomllib.loads() で解析した TOML データ

        Returns:
            ルール ID をキー、有効/無効を値とする dict。セクションが存在しない場合は空 dict
        """
        try:
            tool_section: dict[str, object] = data["tool"]  # type: ignore[assignment]
            paladin_section: dict[str, object] = tool_section["paladin"]  # type: ignore[assignment,index]
            rules_section: dict[str, bool] = paladin_section["rules"]  # type: ignore[assignment,index]
            return {k: bool(v) for k, v in rules_section.items()}
        except KeyError:
            return {}

    def _parse_overrides(self, data: dict[str, object]) -> tuple[OverrideEntry, ...]:
        """TOML データから [[tool.paladin.overrides]] 配列テーブルをパースする

        Args:
            data: tomllib.loads() で解析した TOML データ

        Returns:
            OverrideEntry のタプル。セクションが存在しない場合は空タプル
        """
        try:
            tool_section: dict[str, object] = data["tool"]  # type: ignore[assignment]
            paladin_section: dict[str, object] = tool_section["paladin"]  # type: ignore[assignment,index]
            overrides_list: list[dict[str, object]] = paladin_section["overrides"]  # type: ignore[assignment,index]
        except KeyError:
            return ()

        entries: list[OverrideEntry] = []
        for entry_data in overrides_list:
            files_raw: list[str] = entry_data.get("files", [])  # type: ignore[assignment]
            rules_raw: dict[str, bool] = entry_data.get("rules", {})  # type: ignore[assignment]
            entries.append(
                OverrideEntry(
                    files=tuple(files_raw),
                    rules={k: bool(v) for k, v in rules_raw.items()},
                )
            )
        return tuple(entries)

    def _parse_rule_options(self, data: dict[str, object]) -> dict[str, dict[str, object]]:
        """TOML データから [tool.paladin.rule] セクションをパースする

        Args:
            data: tomllib.loads() で解析した TOML データ

        Returns:
            ルール ID をキー、オプション dict を値とする dict。セクションが存在しない場合は空 dict
        """
        try:
            tool_section: dict[str, object] = data["tool"]  # type: ignore[assignment]
            paladin_section: dict[str, object] = tool_section["paladin"]  # type: ignore[assignment,index]
            rule_section: dict[str, dict[str, object]] = paladin_section["rule"]  # type: ignore[assignment,index]
            return {k: dict(v) for k, v in rule_section.items()}
        except KeyError:
            return {}

    def _parse_per_file_ignores(self, data: dict[str, object]) -> tuple[PerFileIgnoreEntry, ...]:
        """TOML データから per_file_ignores エントリを解析する

        Args:
            data: tomllib.loads() で解析した TOML データ

        Returns:
            PerFileIgnoreEntry のタプル。セクションが存在しない場合は空タプル
        """
        try:
            tool_section: dict[str, object] = data["tool"]  # type: ignore[assignment]
            paladin_section: dict[str, object] = tool_section["paladin"]  # type: ignore[assignment,index]
            per_file_ignores_section: dict[str, list[str]] = paladin_section["per-file-ignores"]  # type: ignore[assignment,index]
        except KeyError:
            return ()

        entries: list[PerFileIgnoreEntry] = []
        for pattern, rule_list in per_file_ignores_section.items():
            if rule_list == ["*"]:
                entries.append(
                    PerFileIgnoreEntry(
                        pattern=pattern,
                        rule_ids=frozenset(),
                        ignore_all=True,
                    )
                )
            else:
                entries.append(
                    PerFileIgnoreEntry(
                        pattern=pattern,
                        rule_ids=frozenset(rule_list),
                        ignore_all=False,
                    )
                )
        return tuple(entries)
