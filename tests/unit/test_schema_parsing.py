from csvmodel.types import SchemaSpec


def test_file_prefix():
    assert SchemaSpec.from_string('file:any_file.py:AnyModel') == SchemaSpec(
        type='file',
        details='any_file.py:AnyModel',
    )


def test_inline_prefix():
    assert SchemaSpec.from_string('inline:{"type": "object"}') == SchemaSpec(
        type='inline',
        details='{"type": "object"}',
    )


def test_module_prefix():
    assert SchemaSpec.from_string('module:any_package.any_module:AnyModel') == SchemaSpec(
        type='module',
        details='any_package.any_module:AnyModel',
    )


def test_no_prefix():
    assert SchemaSpec.from_string('{"type": "object"}') == SchemaSpec(
        type='inline',
        details='{"type": "object"}',
    )
