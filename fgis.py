#fgis.py
from __future__ import annotations

import logging
import random
import asyncio
import datetime
import time
from typing import Dict, Iterable, Optional, Tuple

import httpx
from tqdm import tqdm

from config import cfg


logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, min_interval: float):
        self.min_interval = max(0.0, min_interval)
        self._lock = asyncio.Lock()
        self._last: float = 0.0

    async def acquire(self):
        if self.min_interval <= 0:
            return None

        async with self._lock:
            now = time.monotonic()
            wait = self.min_interval - (now - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


def format_date(value) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None

    for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(value.strip(), fmt).strftime('%Y-%m-%d')

        except ValueError:
            continue

    return None


def _extract_year(cert_num: str) -> str:
    return cert_num.split('/')[1].split('-')[-1]


async def _get_with_retry(
        client: httpx.AsyncClient,
        params: dict,
        cert_num: str,
    ) -> Optional[httpx.Response]:

    max_retries = getattr(cfg.fgis, 'max_retries', 5)
    base_delay = cfg.fgis.retry_delay

    for attempt in range(max_retries + 1):
        try:
            r = await client.get(
                    cfg.fgis.base_url,
                    params=params,
                    timeout=cfg.fgis.timeout,
                )
        except httpx.HTTPError as e:
            if attempt == max_retries:
                return None
            await asyncio.sleep(base_delay * (2 ** attempt))
            continue

        if r.status_code == 200:
            return r

        if r.status_code == 429 or 500 <= r.status_code < 600:
            if attempt == max_retries:
                return r

            retry_after = r.headers.get('Retry-After')
            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = base_delay * (2 ** attempt)
            else:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)

            logger.warning('[%s] %s, await %.1fs', cert_num, r.status_code, delay)
            await asyncio.sleep(delay)
            continue

        return r

    return None


def _normalize_item(item: dict) -> dict:
    if 'verification_date' in item:
        return {
                'ver_date': item.get('verification_date'),
                'valid_date': item.get('valid_date'),
                'mit_title': item.get('mit_title') or '',
            }

    vri = item.get('vriInfo', {})
    mi = item.get('miInfo', {})
    single = mi.get('singleMI') or {}
    return {
            'ver_date': vri.get('vrfDate'),
            'valid_date': vri.get('validDate'),
            'mit_title': single.get('mitypeTitle') or '',
        }


async def fetch_one(
        client: httpx.AsyncClient,
        sem: asyncio.Semaphore,
        limiter: RateLimiter,
        cert_num: str,
        surname: str,
    ) -> Tuple[str, Optional[dict]]:

    year = _extract_year(cert_num)
    params = {'year': year, 'result_docnum': cert_num}

    async with sem:
        try:
            await limiter.acquire()
            r = await _get_with_retry(client, params, cert_num)

            if r is None:
                logger.error('[%s] нет ответа после retry', cert_num)
                return cert_num, None

        except httpx.HTTPError as e:
            logger.exception('[%s] HTTP error', cert_num)

            return cert_num, None

        if r.status_code != 200:
            logger.warning('[%s] status %s', cert_num, r.status_code)

            return cert_num, None

    try:
        result = r.json()['result']
    except (KeyError, IndexError, ValueError) as e:
        logger.warning('[%s] bad response: %s', cert_num, e)

        return cert_num, None

    items = result.get('items')
    if isinstance(items, list) and items:
        raw_item = items[0]
    elif isinstance(items, list) and not items:
        return cert_num, None
    else:
        raw_item = result

    emp = cfg.find_employee(surname)
    if emp is None:
        logger.warning('[%s] нет SNILS для "%s"', cert_num, surname)
        return cert_num, None

    norm = _normalize_item(raw_item)

    
    data = {
            'ver_date': format_date(norm['ver_date']),
            'valid_date': format_date(norm['valid_date']),
            'mit_title': norm['mit_title'],
            'last': emp.last,
            'first': emp.first,
            'snils': emp.snils,
            }

    logger.info('[%s] ver=%s valid=%s "%s"', cert_num, data['ver_date'], data['valid_date'], data['mit_title'])
    
    return cert_num, data


async def fetch_all(
        pairs: Iterable[Tuple[str, str]],
        concurrency: Optional[int] = None,
        min_interval: Optional[float] = None,
    ) -> Dict[str, dict]:

    pairs = list(pairs)
    concurrency = concurrency or cfg.fgis.concurrency
    min_interval=(
            min_interval if min_interval is not None
            else getattr(cfg.fgis, 'min_interval', 0.0)
        )  

    sem = asyncio.Semaphore(concurrency)
    limiter = RateLimiter(min_interval)
    limits = httpx.Limits(
        max_connections=concurrency,
        max_keepalive_connections=concurrency,
                    )

    bar = tqdm(total=len(pairs), desc='FGIS', unit='серт', ncols=100)

    async def _wrapped(client, sem, limiter, num, name):
        try:
            return await fetch_one(client, sem, limiter, num, name)
        finally:
            bar.update(1)
            

    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        tasks = [_wrapped(client, sem, limiter, num, name) for num, name in pairs]
        try:
            results = await asyncio.gather(*tasks)
        finally:
            bar.close()

    data_set = {num: data for num, data in results if data is not None}
    failed = [num for num, data in results if data is None]

    if failed:
        logger.warning('Не получено: %d из %d', len(failed), len(pairs))
        for num in failed:
            logger.warning('  - %s', num)

    return data_set
  
