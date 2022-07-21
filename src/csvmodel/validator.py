from typing import Type, List, Dict, Optional, Any, Union, cast, Tuple
from abc import ABC, abstractmethod

import json

import jsonschema

from .errors import ValidationError
from .types import ValidationResult, SchemaSpec, SchemaSpecType
from .csvfile import CsvFile
from .errors import ConfigError


class Validator(ABC):
    name: str

    @classmethod
    @abstractmethod
    def from_schema(cls, schema: SchemaSpec) -> 'Validator':
        pass

    @abstractmethod
    def check(self, infile: CsvFile) -> ValidationResult:
        pass

    @staticmethod
    def prefix(messages: List[Tuple[int, str]], filename: str) -> List[str]:
        return [f'{filename}:{lineno+1}: {msg}' for lineno, msg in messages]


MixedDict = Dict[str, Union[str, float]]


class JsonSchemaValidator(Validator):
    name: str = 'jsonschema'

    def __init__(self, schema: Dict[str, Any]):
        self._schema = schema

    @classmethod
    def from_schema(cls, schema: SchemaSpec):
        if schema.type == SchemaSpecType.inline:
            return cls(json.loads(schema.details))

        elif schema.type == SchemaSpecType.file:  # pragma: no cover
            with open(schema.details) as f:
                return cls(json.load(f))

    def check(self, infile: CsvFile) -> ValidationResult:
        ok: bool = True
        messages: List[Tuple[int, str]] = []
        header: List[str]

        for i, content in enumerate(infile.iter_rows()):
            if i == 0:
                header = content
            else:
                msg = self._check_line(dict(zip(header, content)))
                if msg:
                    ok = False
                    messages.append((i, msg))

        return ValidationResult(
            ok=ok,
            messages=self.prefix(messages, infile.filename),
        )

    def _check_line(self, record: Dict[str, str]) -> Optional[str]:
        try:
            record_ = self._fix_numbers(record)
            jsonschema.validate(record_, self._schema)
            return None
        except ValidationError as e:
            return e.message
        except jsonschema.ValidationError as e:
            return e.message
        except Exception:
            raise

    def _fix_numbers(self, record: Dict[str, str]) -> MixedDict:
        # There are only quite restricted schemata that are valid for csvs
        # Fix the string only dict here if possible
        record_: MixedDict = cast(MixedDict, record.copy())
        missing = 0
        if 'properties' in self._schema:
            for varname, value in self._schema['properties'].items():
                if varname not in record:
                    missing += 1
                elif 'type' in value:
                    if value['type'] == 'number':
                        try:
                            record_[varname] = float(record[varname])
                        except Exception:
                            record_[varname] = record[varname]
                    elif value['type'] == 'integer':
                        try:
                            record_[varname] = int(record[varname])
                        except Exception:
                            record_[varname] = record[varname]
                    elif value['type'] == 'string':
                        record_[varname] = record[varname]
                    else:
                        raise ValueError('Schema too deep for csv files')

        if missing:
            raise ValidationError(f'Missing {missing} column{"s" if missing > 1 else ""}')
        return record_


def get_validator(name: str, schema: SchemaSpec) -> Validator:
    item: Type[Validator]
    for item in Validator.__subclasses__():  # type: ignore
        if item.name.lower() == name:
            return item.from_schema(schema)  # type: ignore
    raise ConfigError(f'No validator by the name {name}')
