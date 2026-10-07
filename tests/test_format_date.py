#test_format_date.py
from fgis import format_date

def test_dotted_format():
    assert format_date('23.09.2026') == '2026-09-23'


def test_iso_format():
    assert format_date('2026-09-23') == '2026-09-23'


def test_empty_returns_none():
    assert format_date('') is None
    assert format_date(None) is None
    assert format_date(' ') is None


def test_garbage_returns_none():
    assert format_date('not date') is None


def test_non_string_returns_none():
    assert format_date(12345) is None
    assert format_date(['2026-09-23']) is None

