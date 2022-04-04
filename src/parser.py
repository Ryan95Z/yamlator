from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator
from lark import Lark
from lark import Transformer
from lark import UnexpectedInput
from lark.exceptions import VisitError
from typing import Any

from src.types import Rule
from src.types import ContainerTypes
from src.types import YamlerRuleset
from src.types import YamlerEnum
from src.types import YamlerType
from src.types import RuleType
from src.types import EnumItem
from src.types import SchemaTypes
from src.exceptions import ConstructNotFoundError
from src.exceptions import SchemaParseError


_package_dir = Path(__file__).parent.absolute()
_GRAMMER_FILE = os.path.join(_package_dir, 'grammer/grammer.lark')


def parse_rulesets(ruleset_content: str) -> dict:
    """Parses a ruleset into a set of instructions that can be
    used to validate a YAML file.

    Args:
        ruleset_content (str): The string contnet of a ruleset schema

    Returns:
        A `dict` that contains the instructions to validate the YAML file

    Raises:
        ValueError: Raised when `ruleset_content` is `None`
        YamlerParseError: Raised when the parsing process is interrupted
        YamlerSyntaxError: Raised when a syntax error is detected in the schema
    """
    if ruleset_content is None:
        raise ValueError("ruleset_content should not be None")

    lark_parser = Lark.open(_GRAMMER_FILE)
    transformer = YamlerTransformer()

    try:
        tokens = lark_parser.parse(ruleset_content)
        return transformer.transform(tokens)
    except VisitError as ve:
        raise SchemaParseError(ve.__context__)
    except UnexpectedInput as u:
        _handle_syntax_errors(u, lark_parser, ruleset_content)


class YamlerTransformer(Transformer):
    """Transforms the Yamler schema contents into a set of objects that
    can be used to validate a YAML file. This class will be used by Lark
    during the parsing process.

    Each method matches to a terminal or rule in the grammer (.lark) file. E.g the
    method `required_rule` corresponds to the following rule in the grammer:

    required_rule: /[a-zA-Z0-9_]+/ type "required"
                 | /[a-zA-Z0-9_]+/ type
    """

    # Used to track previously seen enums or rulesets to dynamically
    # determine the type of the rule if a enum or ruleset is used
    seen_constructs = {}

    def __init__(self, visit_tokens: bool = True) -> None:
        """YamlerTransformer init

        Args:
            visit_tokens (bool): Should the transformer visit tokens in addition
            to rules. Setting this to False is slightly faster. Defaults to True
        """
        super().__init__(visit_tokens)

    def required_rule(self, tokens: Any) -> Rule:
        """Transforms the required rule tokens in a Rule object"""
        (name, rtype) = tokens
        return Rule(name.value, rtype, True)

    def optional_rule(self, tokens: Any) -> Rule:
        """Transforms the optional rule tokens in a Rule object"""
        (name, rtype) = tokens
        return Rule(name.value, rtype, False)

    def ruleset(self, tokens: Any) -> YamlerRuleset:
        """Transforms the ruleset tokens into a YamlerRuleset object"""
        name = tokens[0].value
        rules = tokens[1:]
        self.seen_constructs[name] = SchemaTypes.RULESET
        return YamlerRuleset(name, rules)

    def start(self, instructions: Iterator[YamlerType]) -> dict:
        """Transforms the instructions into a dict that sorts the rulesets,
        enums and entry point to validate YAML data"""
        root = None
        rules = {}
        enums = {}

        handler_chain = _RulesetInstructionHandler(rules)
        handler_chain.set_next_handler(_EnumInstructionHandler(enums))

        for instruction in instructions:
            handler_chain.handle(instruction)

        root = rules.get('main')
        if root is not None:
            del rules['main']

        return {
            'main': root,
            'rules': rules,
            'enums': enums
        }

    def str_type(self, _: Any) -> RuleType:
        """Transforms a string type token into a RuleType object"""
        return RuleType(type=SchemaTypes.STR)

    def int_type(self, _: Any) -> RuleType:
        """Transforms a int type token into a RuleType object"""
        return RuleType(type=SchemaTypes.INT)

    def float_type(self, _: Any) -> RuleType:
        """Transforms a float type token into a RuleType object"""
        return RuleType(type=SchemaTypes.FLOAT)

    def list_type(self, tokens: Any) -> RuleType:
        """Transforms a list type token into a RuleType object"""
        return RuleType(type=SchemaTypes.LIST, sub_type=tokens[0])

    def map_type(self, tokens: Any) -> RuleType:
        """Transforms a map type token into a RuleType object"""
        return RuleType(type=SchemaTypes.MAP, sub_type=tokens[0])

    def any_type(self, _: Any) -> RuleType:
        """Transforms a any type token into a RuleType object"""
        return RuleType(type=SchemaTypes.ANY)

    def enum_item(self, tokens: Any) -> EnumItem:
        """Transforms a enum item token into a EnumItem object"""
        name, value = tokens
        return EnumItem(name=name.value, value=value.value)

    def enum(self, tokens: Any) -> YamlerEnum:
        """Transforms a enum token into a YamlerEnum object"""
        enums = {}

        name = tokens[0]
        items = tokens[1:]

        for item in items:
            enums[item.value] = item
        self.seen_constructs[name] = SchemaTypes.ENUM
        return YamlerEnum(name.value, enums)

    def container_type(self, token: Any) -> RuleType:
        """Transforms a container type token into a RuleType object

        Raises:
            ConstructNotFoundError: Raised if the enum or ruleset cannot be found
        """
        name = token[0]
        schema_type = self.seen_constructs.get(name)
        if schema_type is None:
            raise ConstructNotFoundError(name)
        return RuleType(type=schema_type, lookup=name)

    def type(self, tokens: Any) -> Any:
        """Extracts the type tokens and passes them through onto
        the next stage in the transformer
        """
        (t, ) = tokens
        return t

    def schema_entry(self, rules: list) -> YamlerRuleset:
        """Transforms the schema entry point token into a YamlerRuleset called
        main that will act as the entry point for validaiting the YAML data
        """
        return YamlerRuleset('main', rules)


class _InstructionHandler:
    _next_handler = None

    def set_next_handler(self, handler: _InstructionHandler) -> _InstructionHandler:
        self._next_handler = handler
        return handler

    def handle(self, instruction: YamlerType) -> None:
        if self._next_handler is not None:
            self._next_handler.handle(instruction)


class _EnumInstructionHandler(_InstructionHandler):
    def __init__(self, enums: dict):
        super().__init__()
        self._enums = enums

    def handle(self, instruction: YamlerType) -> None:
        if instruction.type != ContainerTypes.ENUM:
            super().handle(instruction)
            return

        self._enums[instruction.name] = instruction


class _RulesetInstructionHandler(_InstructionHandler):
    def __init__(self, rulesets: dict):
        super().__init__()
        self._rulesets = rulesets

    def handle(self, instruction: YamlerType) -> None:
        if instruction.type != ContainerTypes.RULESET:
            super().handle(instruction)
            return

        self._rulesets[instruction.name] = instruction


class SchemaSyntaxError(SyntaxError):
    """A generic syntax error in the Yamler content"""

    label = None

    def __str__(self) -> str:
        context, line, column = self.args
        if self.label is None:
            return f'Error on line {line}, column {column}.\n\n{context}'
        return f'{self.label} at line {line}, column {column}.\n\n{context}'


class MalformedRulesetNameError(SchemaSyntaxError):
    """Indicates an error in the ruleset name"""
    label = 'Invalid ruleset name'


class MalformedEnumNameError(SchemaSyntaxError):
    """Indicates an error in the enum name"""
    label = 'Invalid enum name'


class MissingRulesError(SchemaSyntaxError):
    """Indicates that a ruleset or schema block is missing rules"""
    label = 'Missing rules'


def _handle_syntax_errors(u: UnexpectedInput, parser: Lark, content: str) -> None:
    exc_class = u.match_examples(parser.parse, {
        MalformedRulesetNameError: [
            'ruleset foo',
            'ruleset 1234Foo',
            'ruleset FOO',
        ],
        MalformedEnumNameError: [
            'enum foo',
            'enum 1234Foo',
            'enum FOO',
        ],
        MissingRulesError: [
            'ruleset Foo {}',
            'schema {}'
        ]
    }, use_accepts=True)
    if not exc_class:
        raise SchemaSyntaxError(u.get_context(content), u.line, u.column)
    raise exc_class(u.get_context(content), u.line, u.column)