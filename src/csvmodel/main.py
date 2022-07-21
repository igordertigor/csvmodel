"""
Usage:
    csvmodel [options] <filename> ...

Options:
    -c <configfile>,--config=<configfile>
        Config file to read [Default: csvmodel.ini]
    -s <jsonschema>,--json-schema=<jsonschema>
        Set the default validator to jsonschema with a schema read from the
        file specified as argument.
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
    if args['--json-schema']:
        config.add_default_options(
            validator='jsonschema',
            schema=f'file:{args["--json-schema"]}',
        )

    exit_status = 0
    for filename in args['<filename>']:
        validator = get_validator(config.validator, config.schema)
        result = validator.check(CsvFile(filename, config.separator))
        if not result.ok:
            print('\n'.join(result.messages))
            exit_status = 1

    exit(exit_status)
