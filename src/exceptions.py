class InvalidSchemaFilenameError(RuntimeError):
    """When the schema filename does not match the expected pattern"""

    def __init__(self, filename: str) -> None:
        """InvalidSchemaFilenameError init

        Args:
            filename (str): The filename that was invalid
        """
        message = f'{filename} is not a valid ruleset filename'
        super().__init__(message)


class ConstructNotFoundError(RuntimeError):
    def __init__(self, construct_name: str) -> None:
        message = f"Type {construct_name} was not found in the schema definition"
        super().__init__(message)


class SchemaParseError(RuntimeError):
    pass
