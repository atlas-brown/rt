import pytest

from rt.regex.ast import Regex
from rt.regex.parser import Dialect, parse_regex


@pytest.fixture(scope="session")
def parse():
    def _parse(pattern: str, dialect: Dialect = Dialect.ERE_EXTENDED) -> Regex:
        return parse_regex(pattern, dialect=dialect)

    return _parse


@pytest.fixture(scope="session")
def unparse():
    return lambda r: str(r)
