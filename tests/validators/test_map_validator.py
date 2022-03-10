from turtle import rt
import unittest

from unittest.mock import patch, Mock
from parameterized import parameterized
from yamler.types import Data, RuleType, SchemaTypes

from .base import BaseWranglerTest
from yamler.validators import MapValidator


class TestMapWrangler(BaseWranglerTest):
    @parameterized.expand([
        ('with_str_rule_type', 'hello', RuleType(type=SchemaTypes.STR), 1),
        ('with_ruleset_rule_type', {'message': 'hello'}, RuleType(
            type=SchemaTypes.RULESET, lookup='message'
        ), 1),
        ('with_map_rule_type', {'message1': 'wow', 'message2': 'wow'}, RuleType(
            type=SchemaTypes.MAP, sub_type=RuleType(type=SchemaTypes.STR)
        ), 2),
        ('with_nested_map_rule_type', {'hello': {'message1': 'test'}}, RuleType(
            type=SchemaTypes.MAP,
            sub_type=RuleType(
                type=SchemaTypes.MAP,
                sub_type=RuleType(type=SchemaTypes.STR)
            )
        ), 1)
    ])
    @patch('yamler.validators.Validator.validate')
    def test_map_validator(self, name: str, data: Data, rtype: RuleType,
                           expected_parent_call_count: int, mock_parent_wrangler: Mock):
        wrangler = MapValidator(self.violations)
        wrangler.validate(
            key=self.key,
            data=data,
            parent=self.parent,
            rtype=rtype
        )
        self.assertEqual(expected_parent_call_count, mock_parent_wrangler.call_count)


if __name__ == '__main__':
    unittest.main()