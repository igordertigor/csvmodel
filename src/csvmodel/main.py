"""
Usage:
    csvmodel [options] <filename> ...

Options:
    -c <configfile>,--config=<configfile>
        Config file to read [Default: csvmodel.ini]
    -j <jsonschema>,--json-schema=<jsonschema>
        Set the default validator to jsonschema with a schema read from the
        file specified as argument.
    -p <pydanticmodel>,--pydantic-model=<pydanticmodel>
        Set the default validator to pydantic with a model read as specified.
        <pydanticmodel> should be a colon (:) separated tuple of filename and
        model name.
"""
from docopt import docopt
import os
from sys import exit
from io import StringIO
from .validator import get_validator
from .csvfile import CsvFile
from .config import Config


def main():
    args = docopt(__doc__)
    if os.path.exists(args['--config']):
        with open(args['--config']) as f:
            config = Config(f)
    else:
        config = Config(StringIO())
    if args['--json-schema'] and args['--pydantic-model']:
        raise ValueError('Only one of --json-schema or --pydantic-model is valid')
    elif args['--json-schema']:
        config.add_default_options(
            validator='jsonschema',
            schema=f'file:{args["--json-schema"]}',
        )
    elif args['--pydantic-model']:
        config.add_default_options(
            validator='pydantic',
            schema=f'file:{args["--pydantic-model"]}',
        )

    exit_status = 0
    for filename in args['<filename>']:
        validator = get_validator(config.validator(filename), config.schema(filename))
        result = validator.check(CsvFile(filename, config.separator(filename)))
        if not result.ok:
            print('\n'.join(result.messages))
            exit_status = 1

    exit(exit_status)
