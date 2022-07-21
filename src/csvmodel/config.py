from configparser import ConfigParser, SectionProxy
from io import TextIOBase
from .types import SchemaSpec


class Config:
    def __init__(self, cfgfile: TextIOBase):
        self.parser = ConfigParser(default_section='csvmodel')
        self.parser['csvmodel'] = {
            'validator': 'jsonschema',
            'schema': '{"type": "object"}',
            'separator': ',',
        }
        self.parser.read_file(cfgfile)

    def add_default_options(self, **kwargs: str):
        self.parser.read_dict({'csvmodel': kwargs})

    def validator(self, filename: str) -> str:
        return self._get_or_create_section(f'csvmodel.{filename}').get('validator')

    def schema(self, filename: str) -> SchemaSpec:
        return SchemaSpec.from_string(
            self._get_or_create_section(f'csvmodel.{filename}').get('schema')
        )

    def separator(self, filename: str) -> str:
        return self._get_or_create_section(f'csvmodel.{filename}').get('separator')

    def _get_or_create_section(self, name: str) -> SectionProxy:
        if name not in self.parser:
            self.parser.add_section(name)
        return self.parser[name]
