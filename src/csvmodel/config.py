from typing import Optional, List
import os
from configparser import ConfigParser, SectionProxy
from io import TextIOBase
from .types import SchemaSpec


class Config:
    def __init__(self, cfgfile: Optional[TextIOBase]):
        self.parser = ConfigParser(default_section='csvmodel')
        self.parser['csvmodel'] = {
            'validator': 'jsonschema',
            'schema': '{"type": "object"}',
            'separator': ',',
        }
        if cfgfile is not None:
            self.parser.read_file(cfgfile)

    def add_default_options(self, **kwargs: str):
        self.parser.read_dict({'csvmodel': kwargs})

    def validator(self, filename: str) -> str:
        return self._get_or_create_section(filename).get('validator')

    def schema(self, filename: str) -> SchemaSpec:
        return SchemaSpec.from_string(
            self._get_or_create_section(filename).get('schema')
        )

    def separator(self, filename: str) -> str:
        return self._get_or_create_section(filename).get('separator')

    def _get_or_create_section(self, filename: str) -> SectionProxy:
        secname = f'csvmodel:{filename}'
        if secname not in self.parser:
            self.parser.add_section(secname)
        return self.parser[secname]


def find_config_file(explicit: Optional[str]) -> Optional[str]:
    options: List[str] = [
        'csvmodel.ini',
        'tox.ini',
        'setup.cfg',
        os.path.expanduser('~/.csvmodel.ini'),
    ]

    if explicit is not None:
        return explicit

    for option in options:
        if os.path.exists(option):
            return option

    return None
