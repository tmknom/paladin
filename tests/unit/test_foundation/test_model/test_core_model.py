"""CoreModelのテスト"""

import pytest
from pydantic import Field, ValidationError

from example.foundation.model import CoreModel


class SampleCoreModel(CoreModel):
    """テスト用のCoreModelサブクラス"""

    name: str
    value: int
    description: str = Field(alias="desc")


class TestCoreModel:
    """CoreModelのテスト"""

    def test_extra_forbid_異常系_未知フィールドでValidationError(self):
        # Arrange
        data: dict[str, str | int] = {
            "name": "test",
            "value": 42,
            "desc": "test description",
            "unknown_field": "should_not_be_allowed",
        }

        # Act & Assert
        with pytest.raises(ValidationError):
            SampleCoreModel.model_validate(data)

    def test_populate_by_name_正常系_エイリアスとフィールド名の両方で入力可能(self):
        # Arrange
        data_alias: dict[str, str | int] = {"name": "test", "value": 42, "desc": "via alias"}
        data_field: dict[str, str | int] = {
            "name": "test",
            "value": 42,
            "description": "via field name",
        }

        # Act
        obj_alias = SampleCoreModel.model_validate(data_alias)
        obj_field = SampleCoreModel.model_validate(data_field)

        # Assert
        assert obj_alias.description == "via alias"
        assert obj_field.description == "via field name"

    def test_str_strip_whitespace_正常系_文字列前後の空白を自動除去(self):
        # Arrange
        data: dict[str, str | int] = {
            "name": "  test_name  ",
            "value": 42,
            "desc": "\t test description \n",
        }

        # Act
        obj = SampleCoreModel.model_validate(data)

        # Assert
        assert obj.name == "test_name"
        assert obj.description == "test description"

    def test_frozen_異常系_フィールド変更でValidationError(self):
        # Arrange
        obj = SampleCoreModel.model_validate({"name": "test", "value": 42, "desc": "desc"})

        # Act & Assert
        with pytest.raises(ValidationError):
            obj.name = "modified"
