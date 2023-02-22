"""Contains functions to load """

import os
import typing

from yamlator.utils import load_schema
from yamlator.types import RuleType
from yamlator.types import YamlatorSchema
from yamlator.types import YamlatorRuleset
from yamlator.types import YamlatorEnum
from yamlator.types import SchemaTypes
from yamlator.types import PartiallyLoadedYamlatorSchema
from yamlator.parser.core import parse_schema
from yamlator.exceptions import ConstructNotFoundError


def parse_yamlator_schema(schema_path: str) -> YamlatorSchema:
    """Parses a Yamlator schema from a given path on the file system

    Args:
        schema_path (str): The file path to the schema file

    Returns:
        A `yamlator.types.YamlatorSchema` object that contains
        the contents of the schema file in a format that can
        be processed by Yamlator

    Raises:
        ValueError: If the schema path is None, not a string
            or is an empty string

        yamlator.exceptions.InvalidSchemaFilenameError: If the filename
            does not match a file with a `.ys` extension

        yamlator.exceptions.SchemaParseError: Raised when the parsing
            process is interrupted

        yamlator.parser.SchemaSyntaxError: Raised when a syntax error
            is detected in the schema
    """
    if (schema_path is None) or (not isinstance(schema_path, str)):
        raise ValueError('Expected parameter schema_path to be a string')

    schema_content = load_schema(schema_path)
    schema = parse_schema(schema_content)

    context = fetch_schema_path(schema_path)
    schema = load_schema_imports(schema, context)
    return schema


def fetch_schema_path(schema_path: str) -> str:
    """Fetches the current path for a schema file

    Args:
        schema_path (str): The path to the Yamlator schema file

    Returns:
        A string of the path that hosts the schema file

    Raises:
        ValueError: If the parameter `schema_path` is `None` or not
            a string
    """
    if (schema_path is None) or (not isinstance(schema_path, str)):
        raise ValueError('Expected parameter schema_path to be a string')

    context = schema_path.split('\\')[:-1]
    return os.path.join(*context)


def load_schema_imports(loaded_schema: PartiallyLoadedYamlatorSchema,
                        schema_path: str) -> YamlatorSchema:
    """Loads all import statements that have been defined in a Yamlator
    schema file. This function will automatically load any import
    statements from child schema files

    Args:
        loaded_schema (yamlator.types.PartiallyLoadedYamlatorSchema): A schema
            that has been partially loaded by the Lark transformer but has
            not had all the imports resolved

        context (str): The path that contains the Yamlator schema file

    Returns:
        A `yamlator.types.YamlatorSchema` object that has all the types
        resolved

    Raises:
        ValueError: If the `schema_path` is None, not a string or
            `loaded_schema` is `None`

        yamlator.exceptions.InvalidSchemaFilenameError: If the filename
            does not match a file with a `.ys` extension

        yamlator.exceptions.SchemaParseError: Raised when the parsing
            process is interrupted

        yamlator.parser.SchemaSyntaxError: Raised when a syntax error
            is detected in the schema
    """
    if loaded_schema is None:
        raise ValueError('Parameter loaded_schema should not None')

    if (schema_path is None) or (not isinstance(schema_path, str)):
        raise ValueError('Expected parameter schema_path to be a string')

    import_statements = loaded_schema.imports
    root_rulesets = loaded_schema.rulesets
    root_enums = loaded_schema.enums

    for path, resource_type in import_statements.items():
        full_path = os.path.join(schema_path, path)
        schema = parse_yamlator_schema(full_path)

        imported_rulesets = schema.rulesets
        imported_enums = schema.enums

        for resource in resource_type:
            ruleset: YamlatorRuleset = imported_rulesets.get(resource)
            if ruleset is not None:
                root_rulesets[ruleset.name] = ruleset
                continue

            enum: YamlatorEnum = imported_enums.get(resource)
            if enum is not None:
                root_enums[enum.name] = enum
                continue

    unknown_types = loaded_schema.unknowns_rule_types
    ruleset, enums = resolve_unknown_types(unknown_types,
                                           root_rulesets, root_enums)
    return YamlatorSchema(loaded_schema.root, ruleset, enums)


def resolve_unknown_types(unknown_types: 'list[RuleType]',
                          rulesets: dict,
                          enums: dict) -> typing.Tuple[dict, dict]:
    """Resolves any types that are marked as unknown since the ruleset
    or enum was imported into the schema. This function will go through
    each unknown type and populate with the relevant rule type

    Args:
        unknown_types (list[yamlator.types.RuleType]): A list of types that
            have a `schema_type` as `SchemaType.UNKNOWN`

        rulesets (dict): A dictionary of rulesets that have been loaded from
            the import statement defined in the schema

        enums (dict): A dictionary of enums that have been loaded from the
            import statements defined in the schema

    Returns:
        A tuple containing the rulesets and enums from the schema where any
        unknown types have been resolved

    Raises:
        yamlator.exceptions.ConstructNotFoundError: If the ruleset or enum
            type was not found
    """
    while len(unknown_types) > 0:
        curr = unknown_types.pop()
        if enums.get(curr.lookup) is not None:
            curr.schema_type = SchemaTypes.ENUM
            continue

        if rulesets.get(curr.lookup) is not None:
            curr.schema_type = SchemaTypes.RULESET
            continue

        raise ConstructNotFoundError(curr.lookup)
    return rulesets, enums