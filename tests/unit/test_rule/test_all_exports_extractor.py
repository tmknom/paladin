"""AllExports / AllExportsExtractor のユニットテスト"""

import ast
from pathlib import Path

from paladin.rule.all_exports_extractor import AllExports, AllExportsExtractor
from paladin.rule.types import SourceFile


def _sf(source: str, path: str = "src/paladin/__init__.py") -> SourceFile:
    return SourceFile(file_path=Path(path), tree=ast.parse(source), source=source)


class TestAllExports:
    """AllExports 値オブジェクトのテスト"""

    def test_is_defined_正常系_nodeがあるとき真を返すこと(self):
        node = ast.parse("__all__ = []").body[0]
        ae = AllExports(symbols=(), node=node)
        assert ae.is_defined is True

    def test_is_defined_正常系_nodeがNoneのとき偽を返すこと(self):
        ae = AllExports(symbols=(), node=None)
        assert ae.is_defined is False

    def test_is_empty_正常系_シンボルがないとき真を返すこと(self):
        ae = AllExports(symbols=(), node=None)
        assert ae.is_empty is True

    def test_is_empty_正常系_シンボルがあるとき偽を返すこと(self):
        ae = AllExports(symbols=("Foo",), node=None)
        assert ae.is_empty is False

    def test_contains_正常系_含まれるシンボルで真を返すこと(self):
        ae = AllExports(symbols=("Foo", "Bar"), node=None)
        assert "Foo" in ae

    def test_contains_正常系_含まれないシンボルで偽を返すこと(self):
        ae = AllExports(symbols=("Foo",), node=None)
        assert "Baz" not in ae

    def test_len_正常系_シンボル数を返すこと(self):
        ae = AllExports(symbols=("Foo", "Bar"), node=None)
        assert len(ae) == 2

    def test_iter_正常系_シンボルをイテレーションできること(self):
        ae = AllExports(symbols=("Foo", "Bar"), node=None)
        assert list(ae) == ["Foo", "Bar"]


class TestAllExportsExtractorFindAllNode:
    """AllExportsExtractor.find_all_node() のテスト"""

    def test_正常系_Assign定義があるときノードを返すこと(self):
        tree = ast.parse('__all__ = ["Foo"]\n')
        result = AllExportsExtractor().find_all_node(tree)
        assert isinstance(result, ast.Assign)

    def test_正常系_AugAssign定義があるときノードを返すこと(self):
        tree = ast.parse('__all__ = []\n__all__ += ["Foo"]\n')
        result = AllExportsExtractor().find_all_node(tree)
        # 最初に見つかった Assign を返す
        assert result is not None

    def test_正常系_定義なしのときNoneを返すこと(self):
        tree = ast.parse("x = 1\n")
        result = AllExportsExtractor().find_all_node(tree)
        assert result is None

    def test_正常系_AugAssignのみのとき返すこと(self):
        tree = ast.parse('__all__ += ["Foo"]\n')
        result = AllExportsExtractor().find_all_node(tree)
        assert isinstance(result, ast.AugAssign)


class TestAllExportsExtractorExtract:
    """AllExportsExtractor.extract() のテスト"""

    def test_正常系_all定義ありのとき抽出すること(self):
        sf = _sf('__all__ = ["Foo", "Bar"]\n')
        result = AllExportsExtractor().extract(sf)
        assert result.symbols == ("Foo", "Bar")
        assert result.is_defined is True

    def test_正常系_all定義なしのとき空AllExportsを返すこと(self):
        sf = _sf("x = 1\n")
        result = AllExportsExtractor().extract(sf)
        assert result.symbols == ()
        assert result.is_defined is False

    def test_正常系_タプル形式のallを抽出すること(self):
        sf = _sf('__all__ = ("Foo", "Bar")\n')
        result = AllExportsExtractor().extract(sf)
        assert result.symbols == ("Foo", "Bar")

    def test_正常系_文字列以外の要素を無視すること(self):
        sf = _sf('__all__ = ["Foo", 123]\n')
        result = AllExportsExtractor().extract(sf)
        assert result.symbols == ("Foo",)

    def test_エッジケース_空リストのとき空シンボルで定義ありを返すこと(self):
        sf = _sf("__all__ = []\n")
        result = AllExportsExtractor().extract(sf)
        assert result.symbols == ()
        assert result.is_defined is True


class TestAllExportsExtractorHasAllDefinition:
    """AllExportsExtractor.has_all_definition() のテスト"""

    def test_正常系_代入文があるとき真を返すこと(self):
        sf = _sf('__all__ = ["Foo"]\n')
        assert AllExportsExtractor().has_all_definition(sf) is True

    def test_正常系_AugAssignがあるとき真を返すこと(self):
        sf = _sf('__all__ = []\n__all__ += ["Foo"]\n')
        assert AllExportsExtractor().has_all_definition(sf) is True

    def test_正常系_定義なしのとき偽を返すこと(self):
        sf = _sf("x = 1\n")
        assert AllExportsExtractor().has_all_definition(sf) is False


class TestAllExportsExtractorExtractWithReexports:
    """AllExportsExtractor.extract_with_reexports() のテスト"""

    def test_正常系_allシンボルと相対インポートを収集すること(self):
        source = 'from .foo import Bar\n__all__ = ["Baz"]\n'
        sf = _sf(source)
        result = AllExportsExtractor().extract_with_reexports(sf)
        assert "Bar" in result
        assert "Baz" in result

    def test_正常系_絶対インポートは対象外であること(self):
        source = 'from paladin.check import Foo\n__all__ = ["Bar"]\n'
        sf = _sf(source)
        result = AllExportsExtractor().extract_with_reexports(sf)
        assert "Foo" not in result
        assert "Bar" in result

    def test_正常系_空ファイルのとき空セットを返すこと(self):
        sf = _sf("")
        result = AllExportsExtractor().extract_with_reexports(sf)
        assert result == set()
