"""Check 固有の設定解決機能

ルールの有効/無効フィルタリングと、設定ファイルの per-file-ignores による
FileIgnoreDirective の生成を担当する。
"""

import logging
from pathlib import Path, PurePath

from paladin.check.ignore import FileIgnoreDirective
from paladin.config import PerFileIgnoreEntry
from paladin.lint.protocol import Rule

logger = logging.getLogger(__name__)


class RuleFilter:
    """設定ファイルの rules セクションに基づいてルールの有効/無効を解決するフィルター"""

    def resolve_disabled_rules(
        self,
        rules: dict[str, bool],
        known_rule_ids: frozenset[str],
    ) -> frozenset[str]:
        """設定ファイルの rules から無効ルール ID を解決する

        Args:
            rules: ルール ID をキー、有効/無効を値とする dict
            known_rule_ids: 既知のルール ID セット

        Returns:
            無効化されたルール ID の frozenset。未知のルール ID は警告して除外する
        """
        disabled: set[str] = set()
        for rule_id, enabled in rules.items():
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
        per_file_ignores: tuple[PerFileIgnoreEntry, ...],
        file_paths: tuple[Path, ...],
    ) -> tuple[FileIgnoreDirective, ...]:
        """各ファイルパスに対してマッチするパターンを照合し、FileIgnoreDirective を返す

        Args:
            per_file_ignores: ファイルごとのignoreエントリ群
            file_paths: 照合対象のファイルパス群

        Returns:
            マッチしたファイルの FileIgnoreDirective のタプル。マッチしないファイルは含まない
        """
        if not per_file_ignores or not file_paths:
            return ()

        result: list[FileIgnoreDirective] = []
        for file_path in file_paths:
            matched_entries: list[PerFileIgnoreEntry] = [
                entry
                for entry in per_file_ignores
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
