import unittest

from .base import BaseValidatorTest

from unittest.mock import patch, Mock
from parameterized import parameterized

from src.types import Data
from src.types import RuleType
from src.types import SchemaTypes
from src.validators import MapValidator


class TestMapValidator(BaseValidatorTest):
    @parameterized.expand([
        ('with_str_rule_type', 'hello', RuleType(type=SchemaTypes.STR), 1, 0),
        ('with_ruleset_rule_type', {'message': 'hello'}, RuleType(
            type=SchemaTypes.RULESET, lookup='message'
        ), 1, 0),
        ('with_map_rule_type', {'message1': 'wow', 'message2': 'wow'}, RuleType(
            type=SchemaTypes.MAP, sub_type=RuleType(type=SchemaTypes.STR)
        ), 2, 0),
        ('with_nested_map_rule_type', {'hello': {'message1': 'test'}}, RuleType(
            type=SchemaTypes.MAP,
            sub_type=RuleType(
                type=SchemaTypes.MAP,
                sub_type=RuleType(type=SchemaTypes.STR)
            )
        ), 1, 0),
        ('with_map_rule_none_data', None, RuleType(
            type=SchemaTypes.MAP, sub_type=RuleType(type=SchemaTypes.STR),
        ), 0, 1),
        ('with_map_rule_str_data', "hello world", RuleType(
            type=SchemaTypes.MAP, sub_type=RuleType(type=SchemaTypes.STR),
        ), 0, 1),
        ('with_map_rule_list_data', [0, 1, 2], RuleType(
            type=SchemaTypes.MAP, sub_type=RuleType(type=SchemaTypes.STR),
        ), 0, 1),
    ])
    @patch('src.validators.Validator.validate')
    def test_map_validator(self, name: str, data: Data, rtype: RuleType,
                           expected_parent_call_count: int,
                           expected_violation_count: int,
                           mock_parent_validator: Mock):
        validator = MapValidator(self.violations)
        validator.validate(
            key=self.key,
            data=data,
            parent=self.parent,
            rtype=rtype
        )
        self.assertEqual(expected_parent_call_count, mock_parent_validator.call_count)

        actual_violation_count = len(self.violations)
        self.assertEqual(expected_violation_count, actual_violation_count)


if __name__ == '__main__':
    unittest.main()
