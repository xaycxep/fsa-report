#excel_reader.py
from __future__ import annotations

import os
from typing import Dict

import pandas as pd

from config import cfg

def _pick_engine(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    if ext in ('.xlsx'):
        return 'openpyxl'
    raise ValueError(f'Error format Excel: {ext}')

def read_sert_nums(path: str) -> Dict[str, str]:
    engine = _pick_engine(path)

    df = pd.read_excel(
            path,
            header=None,
            skiprows=cfg.excel.header_row,
            usecols=[cfg.excel.cert_col_index, cfg.excel.name_col_index],
            engine=engine,
            dtype=str,
        )

    df.columns = ['cert', 'name']

    df = df.dropna(subset=['cert', 'name'])

    df['cert'] = df['cert'].astype(str).str.strip()
    df['name'] = df['name'].astype(str).str.strip()

    df = df[(df['cert'] != '') & (df['name'] != '')]

    df = df.drop_duplicates(subset='cert', keep='first')

    return dict(zip(df['cert'], df['name']))
