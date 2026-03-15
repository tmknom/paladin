"""設定ファイルからの Ignore 設定読み込み機能

pyproject.toml の [tool.paladin.per-file-ignores] セクションを読み込み、
ファイルパターンごとの ignore 設定を解決する。
"""

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePath

from paladin.check.ignore import FileIgnoreDirective
from paladin.foundation.fs.error import FileSystemError
from paladin.lint.protocol import Rule
from paladin.protocol.fs import TextFileSystemReaderProtocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PerFileIgnoreEntry:
    """per-file-ignores の単一エントリを保持する値オブジェクト"""

    pattern: str
    rule_ids: frozenset[str]
    ignore_all: bool  # ["*"] 指定時に True


@dataclass(frozen=True)
class ProjectConfig:
    """プロジェクト設定を保持する値オブジェクト"""

    per_file_ignores: tuple[PerFileIgnoreEntry, ...] = field(default=())
    rules: dict[str, bool] = field(default_factory=lambda: {})
    include: tuple[str, ...] = field(default=())
    exclude: tuple[str, ...] = field(default=())


class ProjectConfigLoader:
    """pyproject.toml からプロジェクト設定を読み込むローダー"""

    def __init__(self, reader: TextFileSystemReaderProtocol) -> None:
        """ProjectConfigLoader を初期化する

        Args:
            reader: ファイル読み込み用のリーダー
        """
        self._reader = reader

    def load(self) -> ProjectConfig:
        """pyproject.toml を読み込み ProjectConfig を返す

        Returns:
            ProjectConfig。ファイルが存在しない場合やセクションがない場合はデフォルト値を返す
        """
        try:
            content = self._reader.read(Path("pyproject.toml"))
        except FileSystemError:
            return ProjectConfig()

        data = tomllib.loads(content)
        per_file_ignores = self._parse_per_file_ignores(data)
        rules = self._parse_rules(data)
        include, exclude = self._parse_include_exclude(data)
        return ProjectConfig(
            per_file_ignores=per_file_ignores,
            rules=rules,
            include=include,
            exclude=exclude,
        )

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


class RuleFilter:
    """設定ファイルの rules セクションに基づいてルールの有効/無効を解決するフィルター"""

    def resolve_disabled_rules(
        self,
        config: ProjectConfig,
        known_rule_ids: frozenset[str],
    ) -> frozenset[str]:
        """設定ファイルの rules から無効ルール ID を解決する

        Args:
            config: プロジェクト設定
            known_rule_ids: 既知のルール ID セット

        Returns:
            無効化されたルール ID の frozenset。未知のルール ID は警告して除外する
        """
        disabled: set[str] = set()
        for rule_id, enabled in config.rules.items():
            if not enabled:
                if rule_id not in known_rule_ids:
                    logger.warning("Unknown rule ID in [tool.paladin.rules]: %s", rule_id)
                    continue
                disabled.add(rule_id)
        return frozenset(disabled)

    def filter(
        self,
        rules: tuple[Rule, ...],
        disabled_rule_ids: frozenset[str],
    ) -> tuple[Rule, ...]:
        """無効ルール ID に該当するルールを除外したタプルを返す

        Args:
            rules: フィルタリング対象のルールタプル
            disabled_rule_ids: 無効化するルール ID の frozenset

        Returns:
            有効なルールのみを含むタプル
        """
        return tuple(rule for rule in rules if rule.meta.rule_id not in disabled_rule_ids)


class ConfigIgnoreResolver:
    """ProjectConfig のパターンと file_paths を照合して FileIgnoreDirective を生成するリゾルバー

    glob パターンの照合には PurePath.full_match() を使用する。
    ディレクトリ単位のパターン（例: "tests/**"）が絶対パスに対しても
    正しくマッチするよう、相対パターンには自動的に "**/" を前置する。
    """

    def _normalize_glob_pattern(self, pattern: str) -> str:
        if pattern.startswith("/") or pattern.startswith("**/"):
            return pattern
        return "**/" + pattern

    def resolve(
        self,
        config: ProjectConfig,
        file_paths: tuple[Path, ...],
    ) -> tuple[FileIgnoreDirective, ...]:
        """各ファイルパスに対してマッチするパターンを照合し、FileIgnoreDirective を返す

        Args:
            config: プロジェクト設定
            file_paths: 照合対象のファイルパス群

        Returns:
            マッチしたファイルの FileIgnoreDirective のタプル。マッチしないファイルは含まない
        """
        if not config.per_file_ignores or not file_paths:
            return ()

        result: list[FileIgnoreDirective] = []
        for file_path in file_paths:
            matched_entries: list[PerFileIgnoreEntry] = [
                entry
                for entry in config.per_file_ignores
                if PurePath(str(file_path)).full_match(self._normalize_glob_pattern(entry.pattern))
            ]
            if not matched_entries:
                continue

            if any(entry.ignore_all for entry in matched_entries):
                result.append(
                    FileIgnoreDirective(
                        file_path=file_path,
                        ignore_all=True,
                        ignored_rules=frozenset(),
                    )
                )
            else:
                merged_rules: frozenset[str] = frozenset()
                for entry in matched_entries:
                    merged_rules = merged_rules | entry.rule_ids
                result.append(
                    FileIgnoreDirective(
                        file_path=file_path,
                        ignore_all=False,
                        ignored_rules=merged_rules,
                    )
                )
        return tuple(result)
