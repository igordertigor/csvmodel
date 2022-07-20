import pytest
from unittest import mock

from csvmodel.csvfile import CsvFile


@pytest.fixture
def mock_open():
    with mock.patch('csvmodel.csvfile.open') as m:
        yield m


def test_strip_whitespace(mock_open):
    mock_open.return_value.__enter__.return_value = [
        'some,line,with,stuff,   ',
        'other,line,with,stuff,\n',
    ]
    csv_file = CsvFile('any_file', ',')
    assert [
        row for row in csv_file.iter_rows()
    ] == [
        ['some', 'line', 'with', 'stuff', ''],
        ['other', 'line', 'with', 'stuff', ''],
    ]
