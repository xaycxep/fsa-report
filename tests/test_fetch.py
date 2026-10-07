#test_fetch.py
import asyncio

import httpx
import pytest

from fgis import RateLimiter, fetch_one


def _mock_transport(payload, status=200):
    def handler(requests: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=payload)
    return httpx.MockTransport(handler)


async def _run_fetch(payload, status=200,
                     cert_num='С-КД/23-09-2026/560743690',
                     surname='ФАМИЛИЯ'):
    transport = _mock_transport(payload, status)
    async with httpx.AsyncClient(transport=transport) as client:
        sem = asyncio.Semaphore(1)
        limiter = RateLimiter(0.0)
        return await fetch_one(client, sem, limiter, cert_num, surname)


async def test_fetch_format_b():
    payload = {
            'result': {
                    'items': [{
                            'verification_date': '23.09.2026',
                            'valid_date': '22.09.2032',
                            'mit_title': 'Water mits',
                        }]
                }
        }
    num, data = await _run_fetch(payload)
    assert data is not None
    assert data['ver_date'] == '2026-09-23'
    assert data['valid_date'] == '2032-09-22'
    assert data['last'] == 'Фамилия'
    assert data['snils'] == '00000000000'


async def test_fetch_format_a():
    payload = {
            'result': {
                    'vriInfo': {'vrfDate': '23.09.2026', 'validDate': '22.09.2032'},
                    'miInfo': {'singleMI': {'mitypeTitle': 'Water mits'}},
                }
        }
    num, data = await _run_fetch(payload)
    assert data['ver_date'] == '2026-09-23'
    assert data['valid_date'] == '2032-09-22'
    assert data['mit_title'] == 'Water mits'


async def test_fetch_invalid_instrument():
    payload = {
            'result': {
                    'items': [{
                            'verification_date': '23.09.2026',
                            'mit_title': 'Water mits',
                        }]
                }
        }
    num, data = await _run_fetch(payload)
    assert data is not None
    assert data['valid_date'] is None
    assert data['ver_date'] == '2026-09-23'


async def test_fetch_empty_items_returns_none():
    payload = {'result': {'items': []}}
    num, data = await _run_fetch(payload)
    assert data is None


async def test_fetch_unknown_surname_returns_none():
    payload = {
            'result': {'items': [{
                    'verification_date': '23.09.2026',
                    'valid_date': '22.09.2032',
                    'mit_title': 'X',
                }]}
        }
    num, data = await _run_fetch(payload, surname='UNKNOWN')
    assert data is None


async def test_fetch_status_500_returns_none():
    payload = {}
    num, data = await _run_fetch(payload, status=500)
    assert data is None


async def test_fetch_malformed_json_returns_none():
    payload = {'unexcepted': 'structure'}
    num, data = await _run_fetch(payload)
    assert data is None
