from typing import Iterator, List


class CsvFile:
    filename: str
    separator: str

    def __init__(self, filename: str, separator: str = ','):
        self.filename = filename
        self.separator = separator

    def iter_rows(self) -> Iterator[List[str]]:
        with open(self.filename) as f:
            for row in f:
                yield row.strip().split(self.separator)
