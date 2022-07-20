import pytest
from unittest import mock

from csvmodel import errors
from csvmodel.types import SchemaSpec, ValidationResult
from csvmodel.csvfile import CsvFile
from csvmodel.validator import get_validator, JsonSchemaValidator


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
        return JsonSchemaValidator({
            'type': 'object',
            'properties': {
                'col1': {'type': 'string'},
                'col2': {'type': 'number'},
            }
        })

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

    def testerrors_for_deep_schema(self, raw_csv):
        raw_csv.return_value = [
            'col1,col2',
            'a,1',
        ]
        validator = JsonSchemaValidator({
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
        })
        with pytest.raises(ValueError):
            validator.check(CsvFile('any_file.csv'))
