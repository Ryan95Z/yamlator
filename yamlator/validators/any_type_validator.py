"""Validator for the any time data type"""


from yamlator.types import Data
from yamlator.types import RuleType
from yamlator.types import SchemaTypes
from yamlator.validators.base_validator import Validator


class AnyTypeValidator(Validator):
    """Validator to handle the `any` type. This type ignores all type checks"""

    def validate(self, key: str, data: Data, parent: str, rtype: RuleType,
                 is_required: bool = False) -> None:
        """Validate any rules that have the data marked as the `any` type

        Args:
            key              (str): The key to the data
            data            (Data): The data to validate
            parent           (str): The parent key of the data
            rtype       (RuleType): The type assigned to the rule
            is_required     (bool): Is the rule required
        """

        is_any_type = (rtype.schema_type == SchemaTypes.ANY)
        if is_any_type:
            return

        super().validate(key, data, parent, rtype, is_required)
