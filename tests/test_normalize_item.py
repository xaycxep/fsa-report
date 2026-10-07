#test_normalize_item.py
from fgis import _normalize_item


def test_format_b_flat():
    item = {
            'verification_date': '23.09.2026',
            'valid_date': '22.09.2032',
            'mit_title': 'Water mits',
        }
    norm = _normalize_item(item)
    assert norm['ver_date'] == '23.09.2026'
    assert norm['valid_date'] == '22.09.2032'
    assert norm['mit_title'] == 'Water mits'


def test_format_b_without_valid_date():
    item = {
            'verification_date': '23.09.2026',
            'mit_title': 'Water mits',
        }
    norm = _normalize_item(item)
    assert norm['ver_date'] == '23.09.2026'
    assert norm['valid_date'] is None
    assert norm['mit_title'] == 'Water mits'


def test_format_a_nested():
    item = {
            'vriInfo': {'vrfDate': '23.09.2026', 'validDate': '22.09.2032'},
            'miInfo': {'singleMI': {'mitypeTitle': 'Water mits'}},
        }
    norm = _normalize_item(item)
    assert norm['ver_date'] == '23.09.2026'
    assert norm['valid_date'] == '22.09.2032'
    assert norm['mit_title'] == 'Water mits'


def test_format_a_without_singleMI():
    item = {'vriInfo': {'vrfDate': '23.09.2026', 'validDate': '22.09.2032'}}
    norm = _normalize_item(item)
    assert norm['mit_title'] == ''


def test_empty_item_returns_empty():
    norm = _normalize_item({})
    assert norm['ver_date'] is None
    assert norm['valid_date'] is None
    assert norm['mit_title'] == ''


