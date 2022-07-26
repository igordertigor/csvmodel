import pytest
from unittest import mock

import os
from pydantic import BaseModel, root_validator
import tempfile

from csvmodel import errors
from csvmodel.types import SchemaSpec, ValidationResult
from csvmodel.csvfile import CsvFile
from csvmodel.validator import get_validator, JsonSchemaValidator, PydanticValidator


@pytest.fixture
def inlinespec():
    return SchemaSpec(type='inline', details='{"type": "object"}')


def test_get_validator_for_jsonschema(inlinespec):
    assert isinstance(
        get_validator('jsonschema', inlinespec),
        JsonSchemaValidator,
    )


def test_error_for_requesting_validator():
    with pytest.raises(errors.ConfigError):
        get_validator('validator', inlinespec)


@pytest.fixture
def raw_csv():
    with mock.patch('csvmodel.csvfile.open') as m:
        yield m.return_value.__enter__


class TestJsonSchemaValidator:
    @pytest.fixture
    def validator(self):
        return JsonSchemaValidator(
            {
                'type': 'object',
                'properties': {
                    'col1': {'type': 'string'},
                    'col2': {'type': 'number'},
                },
                'required': ['col1', 'col2'],
            },
            line_limit=1000,
        )

    @pytest.fixture
    def validator2(self):
        return JsonSchemaValidator(
            {
                'type': 'object',
                'properties': {
                    'col1': {'type': 'number'},
                    'col2': {'type': 'integer'},
                },
                'required': ['col1', 'col2'],
            },
            line_limit=1000,
        )

    def test_check_ok_file_gives_no_error(self, validator, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a,1',
        ]
        expected = ValidationResult(ok=True, messages=[])
        assert validator.check(CsvFile('any_file.csv')) == expected

    def test_check_error_messages(self, validator, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a,a'
        ]
        res = validator.check(CsvFile('any_file.csv'))

        assert not res.ok
        assert all([
            msg.startswith('any_file.csv')
            for msg in res.messages
        ])
        assert len(res.messages) == 1
        assert res.messages[0] == "any_file.csv:2: 'a' is not of type 'number'"

    def test_check_missing_values(self, validator, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a'
        ]
        res = validator.check(CsvFile('any_file.csv'))

        assert not res.ok
        assert all([
            msg.startswith('any_file.csv')
            for msg in res.messages
        ])
        assert len(res.messages) == 1
        assert res.messages[0] == "any_file.csv:2: 'col2' is a required property"

    def test_check_integer_works(self, validator2, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            '1.1,1',  # ok
            '1,1.1',  # no ok
        ]
        res = validator2.check(CsvFile('any_file.csv'))
        assert not res.ok
        assert res.messages == [
            "any_file.csv:3: '1.1' is not of type 'integer'",
        ]

    def test_correct_line_numbers(self, validator, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a',
            'a,1',
            'a,a'
        ]
        res = validator.check(CsvFile('any_file.csv'))
        assert not res.ok
        assert all([
            msg.startswith('any_file.csv')
            for msg in res.messages
        ])
        assert len(res.messages) == 2
        assert res.messages[0] == "any_file.csv:2: 'col2' is a required property"
        assert res.messages[1] == "any_file.csv:4: 'a' is not of type 'number'"

    def testerrors_for_deep_schema(self, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a,1',
        ]
        validator = JsonSchemaValidator(
            {
                'type': 'object',
                'properties': {
                    'col1': {'type': 'string'},
                    'col2': {
                        'type': 'object',
                        'properties': {
                            'a': {'type': 'string'},
                            'b': {'type': 'number'},
                         }
                    }
                }
            },
            line_limit=1000,
        )
        with pytest.raises(ValueError):
            validator.check(CsvFile('any_file.csv'))


class TestPydanticValidator:
    @pytest.fixture
    def model(self):

        class Data(BaseModel):
            col1: str
            col2: int

        return Data

    @pytest.fixture
    def model2(self):

        class Data(BaseModel):
            col1: str
            col2: int
            col3: float

        return Data

    def test_ok_data(self, model, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a,1',
        ]
        validator = PydanticValidator(model, line_limit=1000)
        res = validator.check(CsvFile('any_file.csv'))
        assert res.ok

    def test_with_line_limit(self, model, raw_csv):
        raw_csv.return_value = ['col1,col2'] + ['a,1']*19 + ['a,a']
        validator = PydanticValidator(model, line_limit=20)
        res = validator.check(CsvFile('any_file.csv'))
        assert res.ok

    def test_with_line_limit_failure(self, model, raw_csv):
        raw_csv.return_value = ['col1,col2'] + ['a,1']*18 + ['a,a']
        validator = PydanticValidator(model, line_limit=20)
        res = validator.check(CsvFile('any_file.csv'))
        assert not res.ok

    def test_with_single_violation(self, model, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a,a',
        ]
        validator = PydanticValidator(model, line_limit=1000)
        res = validator.check(CsvFile('any_file.csv'))
        assert not res.ok
        assert res.messages == [
            'any_file.csv:2: Issue in column col2: value is not a valid integer'
        ]

    def test_with_multiple_violations(self, model2, raw_csv):
        raw_csv.return_value = [
            'col1,col2,col3',
            'a,1.1,a',
        ]
        validator = PydanticValidator(model2, line_limit=1000)
        res = validator.check(CsvFile('any_file.csv'))
        assert not res.ok
        assert res.messages == [
            'any_file.csv:2: Issue in column col2: value is not a valid integer',
            'any_file.csv:2: Issue in column col3: value is not a valid float'
        ]

    def test_load_schema_from_file(self, raw_csv):
        with tempfile.TemporaryDirectory() as tdir:
            fname = os.path.join(tdir, 'model.py')
            with open(fname, 'w') as f:
                f.write('\n'.join([
                    'from pydantic import BaseModel',
                    '',
                    'class Model(BaseModel):',
                    '    col1: str',
                    '    col2: int',
                    '    col3: float',
                ]))

            validator = PydanticValidator.from_schema(
                SchemaSpec(
                    type='file',
                    details=':'.join([fname, 'Model'])
                ),
            )

        raw_csv.return_value = [
            'col1,col2,col3',
            'a,1,1',
            'a,1.1,a',
            'a,1',
        ]

        res = validator.check(CsvFile('any_file.csv'))

        assert not res.ok
        assert res.messages == [
            'any_file.csv:3: Issue in column col2: value is not a valid integer',
            'any_file.csv:3: Issue in column col3: value is not a valid float',
            'any_file.csv:4: Issue in column col3: field required',
        ]

    def test_missing_field(self, model, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a',
        ]
        validator = PydanticValidator(model, line_limit=1000)
        res = validator.check(CsvFile('any_file.csv'))
        assert not res.ok
        assert res.messages == [
            'any_file.csv:2: Issue in column col2: field required'
        ]

    def test_root_validator(self, raw_csv):

        class Model(BaseModel):
            col1: int
            col2: int

            @root_validator(pre=False)
            def only_one_nonzero(cls, values):
                col1 = int(values.get('col1'))
                col2 = int(values.get('col2'))
                if col1*col2 != 0:
                    raise ValueError('Either col1 or col2 should be 0')
                return values

        raw_csv.return_value = [
            'col1,col2',
            '1,1',
            '3,0',
        ]

        validator = PydanticValidator(Model, line_limit=1000)
        res = validator.check(CsvFile('any_file.csv'))

        assert not res.ok
        assert res.messages == [
            'any_file.csv:2: Issue in column __root__: Either col1 or col2 should be 0',
        ]

    def test_validator_from_module(self, raw_csv):
        validator = PydanticValidator.from_schema(
            SchemaSpec(
                type='module',
                details='csvmodel.testing:ExampleModel',
            )
        )

        raw_csv.return_value = [
            'col1,col2,col3',
            '1,a,3.2',
            '3.3,a,b',
        ]

        res = validator.check(CsvFile('any_file.csv'))
        assert not res.ok
        assert res.messages == [
            'any_file.csv:3: Issue in column col1: value is not a valid integer',
            'any_file.csv:3: Issue in column col3: value is not a valid float',
        ]

    def test_validator_from_nonexistant_file(self):
        with pytest.raises(errors.NoSchemaError):
            PydanticValidator.from_schema(
                SchemaSpec(
                    type='file',
                    details='non_existant_file.py:Model',
                )
            )

    def test_nonexistant_model(self):
        with pytest.raises(errors.NoSchemaError):
            PydanticValidator.from_schema(
                SchemaSpec(
                    type='module',
                    details='csvmodel.testing:DoesNotExist',
                )
            )

    def test_pydantic_dataclasses(self, raw_csv):
        with tempfile.TemporaryDirectory() as tdir:
            fname = os.path.join(tdir, 'model.py')
            with open(fname, 'w') as f:
                f.write('\n'.join([
                    'from pydantic.dataclasses import dataclass',
                    '',
                    '@dataclass',
                    'class Model:',
                    '    col1: str',
                    '    col2: int',
                    '    col3: float',
                ]))

            validator = PydanticValidator.from_schema(
                SchemaSpec(
                    type='file',
                    details=':'.join([fname, 'Model'])
                )
            )

        raw_csv.return_value = [
            'col1,col2,col3',
            'a,1,1',
            'a,1.1,a',
            'a,1',
        ]

        res = validator.check(CsvFile('any_file.csv'))

        assert not res.ok
        assert res.messages == [
            'any_file.csv:3: Issue in column col2: value is not a valid integer',
            'any_file.csv:3: Issue in column col3: value is not a valid float',
            "any_file.csv:4: missing 1 required positional argument: 'col3'",
        ]
