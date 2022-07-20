"""
Usage:
    csvmodel [options] <filename> ...

Options:
    -c <configfile>,--config=<configfile>
        Config file to read
"""
from docopt import docopt
from sys import exit
from .validator import get_validator
from .csvfile import CsvFile
from .config import Config


def main():
    args = docopt(__doc__)
    with open(args['--config']) as f:
        config = Config(f)

    exit_status = 0
    for filename in args['<filename>']:
        validator = get_validator(config.validator, config.schema)
        result = validator.check(CsvFile(filename, config.separator))
        if not result.ok:
            print('\n'.join(result.messages))
            exit_status = 1

    exit(exit_status)
