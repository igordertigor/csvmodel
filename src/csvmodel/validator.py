from typing import Type, List, Dict, Any, Union, cast, Tuple
from types import ModuleType
from abc import ABC, abstractmethod

import json
import jsonschema

import os
import random
import importlib
import importlib.util
import pydantic

from .errors import NoSchemaError
from .types import ValidationResult, SchemaSpec, SchemaSpecType
from .csvfile import CsvFile
from .errors import ConfigError


class Validator(ABC):
    name: str

    @classmethod
    @abstractmethod
    def from_schema(cls, schema: SchemaSpec) -> 'Validator':
        pass

    def check(self, infile: CsvFile) -> ValidationResult:
        ok: bool = True
        messages: List[Tuple[int, str]] = []
        header: List[str]

        for i, content in enumerate(infile.iter_rows()):
            if i == 0:
                header = content
            else:
                msg = self.check_line(dict(zip(header, content)))
                if len(msg):
                    ok = False
                    messages.extend([(i, m) for m in msg])

        return ValidationResult(
            ok=ok,
            messages=self.prefix(messages, infile.filename),
        )

    @abstractmethod
    def check_line(self, record: Dict[str, str]) -> List[str]:
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
    def from_schema(cls, schema: SchemaSpec) -> 'JsonSchemaValidator':
        if schema.type == SchemaSpecType.inline:
            return cls(json.loads(schema.details))

        elif schema.type == SchemaSpecType.file:  # pragma: no cover
            with open(schema.details) as f:
                return cls(json.load(f))

        elif schema.type == SchemaSpecType.module:  # pragma: no cover
            raise ValueError('Schema from module is not supported by jsonschema')

        raise ValueError('This should never happen')  # pragma: no cover

    def check_line(self, record: Dict[str, str]) -> List[str]:
        try:
            record_ = self._fix_numbers(record)
            jsonschema.validate(record_, self._schema)
            return []
        except jsonschema.ValidationError as e:
            return [e.message]
        except Exception:
            raise

    def _fix_numbers(self, record: Dict[str, str]) -> MixedDict:
        # There are only quite restricted schemata that are valid for csvs
        # Fix the string only dict here if possible
        record_: MixedDict = cast(MixedDict, record.copy())
        if 'properties' in self._schema:
            for varname, value in self._schema['properties'].items():
                if varname not in record:
                    continue
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

        return record_


class PydanticValidator(Validator):
    name: str = 'pydantic'
    _model: pydantic.BaseModel

    def __init__(self, model: pydantic.BaseModel):
        self._model = model

    @classmethod
    def from_schema(cls, schema: SchemaSpec) -> 'PydanticValidator':
        if schema.type == SchemaSpecType.inline:  # pragma: no cover
            raise ValueError('Inline schema is not supported for pydantic')
        elif schema.type == SchemaSpecType.file:
            origin, classname = schema.details.split(':')
            module = cls._import_module_from_filename(origin)

        elif schema.type == SchemaSpecType.module:
            origin, classname = schema.details.split(':')
            module = cls._import_module(origin)

        try:
            model = getattr(module, classname)
        except AttributeError:
            raise NoSchemaError(f'No class called {classname} in {origin}')

        return cls(model)

    def check_line(self, record: Dict[str, str]) -> List[str]:
        try:
            self._model(**record)
            return []
        except pydantic.ValidationError as e:
            out: List[str] = []
            for issue in e.errors():
                colnames = ','.join(issue["loc"])
                out.append(f'Issue in column {colnames}: {issue["msg"]}')
            return out
        except TypeError as e:
            message = e.args[0]
            if message.startswith(self._model.__name__):  # pragma: no cover
                message = message[len(self._model.__name__)+1:]
            if message.startswith('__init__() '):
                message = message[len('__init__() '):]
            return [message]

    @staticmethod
    def _import_module(name: str) -> ModuleType:
        return importlib.import_module(name)

    @staticmethod
    def _import_module_from_filename(filename: str):
        module_name = f'csvmodel.schema_{random.randint(1, 100000)}'
        if not os.path.exists(filename):
            raise NoSchemaError(f'No schema file {filename} found')
        spec = importlib.util.spec_from_file_location(module_name, filename)
        if spec is None:  # pragma: no cover
            raise NoSchemaError(f'Failed to import schema from {filename}')
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:  # pragma: no cover
            raise NoSchemaError(f'Failed to import schema from {filename}')
        spec.loader.exec_module(module)
        return module


def get_validator(name: str, schema: SchemaSpec) -> Validator:
    item: Type[Validator]
    for item in Validator.__subclasses__():  # type: ignore
        if item.name.lower() == name:
            return item.from_schema(schema)  # type: ignore
    raise ConfigError(f'No validator by the name {name}')
