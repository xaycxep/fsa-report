#config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import yaml


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    directory: str
    file: str
    max_bytes: int
    backup_count: int
    console: bool


@dataclass(frozen=True)
class FgisConfig:
    base_url: str
    concurrency: int
    timeout: float
    retry_on_429: bool
    retry_delay: float
    max_retries: int = 5
    min_interval: float = 0.0

    def __post_init__(self):
        if self.concurrency < 1:
            raise ValueError(f'concurrency: {self.concurrency} < 1')

        if self.timeout <= 0:
            raise ValueError(f'timeout: {self.timeout} <= 0')

        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError(f"base_url not 'http://', 'https://': {self.base_url}")


@dataclass(frozen=True)
class ExcelConfig:
    cert_col_index: int
    name_col_index: int
    header_row: int


@dataclass(frozen=True)
class OutputConfig:
    xml_file: str


@dataclass(frozen=True)
class Employee:
    last: str
    first: str
    snils: str


@dataclass(frozen=True)
class Config:
    fgis: FgisConfig
    excel: ExcelConfig
    output: OutputConfig
    logging: LoggingConfig
    snils_data: Dict[str, Employee]


    def find_employee(self, surname: str) -> Employee | None:
        if not surname:
            return None
        return self.snils_data.get(surname.strip().upper())


DEFAULT_PATH = Path(__file__).parent / 'config.yml'


def load_config(path: str | os.pathLike | None = None) -> Config:
    path = Path(path) if path else DEFAULT_PATH
    if not path.exists():
        raise FileNotFoundError(f'Not config file: {path}')

    with path.open('r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError('Err config.yml')

    try:
        return Config(
            fgis=FgisConfig(**raw['fgis']),
            excel=ExcelConfig(**raw['excel']),
            output=OutputConfig(**raw['output']),
            logging=LoggingConfig(**raw.get('logging', {})),
            snils_data={
                    key.upper(): Employee(**val)
                    for key, val in raw.get('snils_data', {}).items()
                },
            )

    except KeyError as e:
        raise KeyError(f'in config.yml not: {e}') from e

    except TypeError as e:
        raise TypeError(f'Err config.yml: {e}') from e

cfg = load_config(os.environ.get('FGIS_CONFIG'))

    
