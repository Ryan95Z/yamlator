import argparse
import json

from abc import ABC
from typing import Iterator
from enum import Enum

from src.parser import SchemaSyntaxError, parse_rulesets
from src.validators import validate_yaml
from src.utils import load_yaml_file
from src.utils import load_schema
from src.exceptions import InvalidSchemaFilenameError, SchemaParseError
from src.violations import ViolationJSONEncoder, ViolationType


SUCCESS = 0
ERR = -1


def main() -> int:
    """Entry point into the Yamler CLI

    Returns:
        A status code where 0 = success and -1 = error
    """
    parser = _create_args_parser()
    args = parser.parse_args()
    violations = []

    try:
        violations = validate_yaml_data_from_file(args.file, args.ruleset_schema)
    except SchemaParseError as ex:
        print(ex)
        return ERR
    except SchemaSyntaxError as ex:
        print(ex)
        return ERR
    except FileNotFoundError as ex:
        print(ex)
        return ERR
    except InvalidSchemaFilenameError as ex:
        print(ex)
        return ERR
    except ValueError as ex:
        print(ex)
        return ERR

    display_method = DisplayMethod[args.output.upper()]
    return display_violations(violations, display_method)


def _create_args_parser():
    description = 'A YAML validation tool that determines if a YAML file matches a given schema'  # nopep8

    parser = argparse.ArgumentParser(prog="yamler", description=description)
    parser.add_argument('file', type=str,
                        help='The YAML file to be validated')

    parser.add_argument('-s', '--schema', type=str, required=True, dest='ruleset_schema',
                        help='The schama that will be used to validate the YAML file')

    parser.add_argument('-o', '--output', type=str, required=False, default='table',
                        choices=['table', 'json'],
                        help='Defines the format that will be displayed for the violations')  # nopep8
    return parser


def validate_yaml_data_from_file(yaml_filepath: str,
                                 yamler_filepath: str) -> Iterator[ViolationType]:
    """Validate a YAML file with a yamler schema file

    Args:
        yaml_filepath   (str): The path to the YAML data file
        yamler_filepath (str): The path to the yamler file

    Returns:
        A Iterator collection of ViolationType objects that contains
        the violations detected in the YAML data against the rulesets.

    Raises:
        ValueError: If either argument is `None` or an empty string
        FileNotFoundError: If either argument cannot be found on the file system
        InvalidYamlerFilenameError: If `yamler_filepath` does not have a valid filename
        that ends with the `.yamler` extension.
    """
    yaml_data = load_yaml_file(yaml_filepath)
    ruleset_data = load_schema(yamler_filepath)

    instructions = parse_rulesets(ruleset_data)
    return validate_yaml(yaml_data, instructions)


class DisplayMethod(Enum):
    """Represents the supported violation display methods"""
    TABLE = "table"
    JSON = "json"


def display_violations(violations: Iterator[ViolationType],
                       method: DisplayMethod = DisplayMethod.TABLE) -> int:
    """Displays the violations to standard output

    Args:
        violations (Iterator[ViolationType]): A collection of violations

        method               (DisplayMethod): Defines how the violations will be
        displayed. By default table will be used specified

    Returns:
        The status code if violations were found. 0 = no violations were found
        and -1 = violations were found

    Raises:
        ValueError: If `violations` or `method` is None
    """
    if violations is None:
        raise ValueError("violations should not be None")

    if method is None:
        raise ValueError("method should not be None")

    if method == DisplayMethod.JSON:
        return JSONOutput.display(violations)
    return TableOutput.display(violations)


class ViolationOutput(ABC):
    """Base class for displaying violations"""

    def display(violations: Iterator[ViolationType]) -> int:
        """Display the violations to the user

        Args:
            violations (Iterator[ViolationType]): A collection of violations

        Returns:
            The status code if violations were found. 0 = no violations were found
            and -1 = violations were found
        """
        pass


class TableOutput(ViolationOutput):
    """Displays violations as a table"""

    def display(violations: Iterator[ViolationType]) -> int:
        """Display the violations to the user as a table

        Args:
            violations (Iterator[ViolationType]): A collection of violations

        Returns:
            The status code if violations were found. 0 = no violations were found
            and -1 = violations were found
        """
        violation_count = len(violations)
        print("\n{:<4} violation(s) found".format(violation_count))

        has_violations = violation_count != 0
        if not has_violations:
            return SUCCESS

        print('\n{:<30} {:<20} {:<15} {:20}'.format(
                'Parent Key', 'Key', 'Violation', 'Message'))
        print('---------------------------------------------------------------------------')  # nopep8
        for violation in violations:
            print('{:<30} {:<20} {:<15} {:20}'.format(
                violation.parent,
                violation.key,
                violation.violation_type,
                violation.message))
        print('---------------------------------------------------------------------------')  # nopep8
        return ERR


class JSONOutput(ViolationOutput):
    """Displays violations as JSON"""

    def display(violations: Iterator[ViolationType]) -> int:
        """Display the violations to the user as JSON

        Args:
            violations (Iterator[ViolationType]): A collection of violations

        Returns:
            The status code if violations were found. 0 = no violations were found
            and -1 = violations were found
        """
        violation_count = len(violations)
        pre_json_data = {'violatons': violations, 'violation_count': violation_count}

        json_data = json.dumps(pre_json_data, cls=ViolationJSONEncoder, indent=4)
        print(json_data)

        return SUCCESS if violation_count == 0 else ERR