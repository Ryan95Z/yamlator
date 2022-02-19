import unittest

from .base import BaseWranglerTest
from unittest.mock import MagicMock
from parameterized import parameterized
from yamler.wranglers import ListWrangler
from yamler.types import RuleType


class TestListWrangler(BaseWranglerTest):
    def setUp(self):
        super().setUp()
        self.mock_ruleset_wrangler = MagicMock()
        self.mock_ruleset_wrangler.wrangle.return_value = None

    @parameterized.expand([
        ('with_non_list_type', RuleType(type=str), 'hello', 0),
        ('with_list_type', RuleType(type=list, sub_type=RuleType(int)), [0, 1, 2, 3], 4),
        ('with_ruleset_list_type', RuleType(
            type=list, sub_type=RuleType(
                type='ruleset', lookup='message'
            )
        ), [{'msg': 'hello'}, {'msg': 'world'}], 2),
        ('with_nested_list', RuleType(
            type=list, sub_type=RuleType(
                type=list, sub_type=RuleType(
                    type=int)
                )
        ), [[0, 1, 2], [3, 4, 5]], 8)
    ])
    def test_list_wrangler(self, name: str, rtype: RuleType, data: str,
                           ruleset_wrangler_call_count: int):
        wrangler = ListWrangler(self.violation_manager)
        wrangler.set_ruleset_wrangler(self.mock_ruleset_wrangler)

        wrangler.wrangle(
            key=self.key,
            data=data,
            parent=self.parent,
            rtype=rtype)

        self.assertEqual(
            ruleset_wrangler_call_count,
            self.mock_ruleset_wrangler.wrangle.call_count
        )


if __name__ == '__main__':
    unittest.main()
