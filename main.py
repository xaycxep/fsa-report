#main.py
import logging
import asyncio
import tkinter as tk
from tkinter import filedialog

from config import cfg
from excel_reader import read_sert_nums
from fgis import fetch_all
from xml_builder import build_xml

from logging_setup import setup_logging


def pick_excel_file() -> str:
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
            title='Select Excel',
            filetypes=[('Excel file', '*.xlsx'), ('All files', '*.*')],
        )
    root.destroy()

    return path


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    path = pick_excel_file()

    if not path:
        logger.warning('Not file')
        return

    sert_nums = read_sert_nums(path)
    data_set = asyncio.run(fetch_all(sert_nums.items()))

    if not data_set:
        logger.error('Not data')
        return

    
    build_xml(data_set)


if __name__ == '__main__':
    main()
