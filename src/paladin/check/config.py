"""設定ファイルからの Ignore 設定読み込み機能

pyproject.toml の [tool.paladin.per-file-ignores] セクションを読み込み、
ファイルパターンごとの ignore 設定を解決する。
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePath

from paladin.check.ignore import FileIgnoreDirective
from paladin.foundation.fs.error import FileSystemError
from paladin.protocol.fs import TextFileSystemReaderProtocol


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

        try:
            data = tomllib.loads(content)
            per_file_ignores = self._parse_per_file_ignores(data)
            return ProjectConfig(per_file_ignores=per_file_ignores)
        except KeyError:
            return ProjectConfig()

    def _parse_per_file_ignores(self, data: dict[str, object]) -> tuple[PerFileIgnoreEntry, ...]:
        """TOML データから per_file_ignores エントリを解析する

        Args:
            data: tomllib.loads() で解析した TOML データ

        Returns:
            PerFileIgnoreEntry のタプル

        Raises:
            KeyError: [tool][paladin][per-file-ignores] セクションが存在しない場合
        """
        tool_section: dict[str, object] = data["tool"]  # type: ignore[assignment]
        paladin_section: dict[str, object] = tool_section["paladin"]  # type: ignore[assignment,index]
        per_file_ignores_section: dict[str, list[str]] = paladin_section["per-file-ignores"]  # type: ignore[assignment,index]

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


class ConfigIgnoreResolver:
    """ProjectConfig のパターンと file_paths を照合して FileIgnoreDirective を生成するリゾルバー"""

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
                if PurePath(str(file_path)).match(entry.pattern)
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
