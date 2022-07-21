from io import StringIO

from csvmodel.types import SchemaSpec, SchemaSpecType

from csvmodel.config import Config


def test_default_parses_schema_correctly():
    default_config = Config(StringIO())
    assert default_config.schema('any_file') == SchemaSpec(
        type=SchemaSpecType.inline,
        details='{"type": "object"}',
    )


def test_successfully_parse_file_schema():
    config = Config(StringIO('\n'.join([
        '[csvmodel]',
        'schema = file:schema.json',
    ])))
    assert config.schema('any_file') == SchemaSpec(
        type=SchemaSpecType.file,
        details='schema.json',
    )


def test_successfully_parse_explcit_inline_schema():
    config = Config(StringIO('\n'.join([
        '[csvmodel]',
        'schema = inline:{"type": "object"}',
    ])))
    assert config.schema('any_file') == SchemaSpec(
        type=SchemaSpecType.inline,
        details='{"type": "object"}',
    )


def test_separate_file_configs():
    config = Config(StringIO('\n'.join([
        '[csvmodel:my_special_file]',
        'validator = pydantic',
        'schema = file:schema.py:MyModel',
        'separator = ;',
    ])))

    # Defaults
    assert config.schema('any_file') == SchemaSpec(
        type=SchemaSpecType.inline,
        details='{"type": "object"}',
    )
    assert config.validator('any_file') == 'jsonschema'
    assert config.separator('any_file') == ','

    # my special file
    assert config.schema('my_special_file') == SchemaSpec(
        type=SchemaSpecType.file,
        details='schema.py:MyModel',
    )
    assert config.validator('my_special_file') == 'pydantic'
    assert config.separator('my_special_file') == ';'
