#logging_setup.py
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from tqdm import tqdm

from config import cfg


class _TqdmHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            tqdm.write(self.format(record), file=sys.stderr)
        except Exception:
            self.handlError(record)


def setup_logging(
        level: str | None = None,
        console: bool | None = None,
    ):
    log_cfg = cfg.logging
    level = level or log_cfg.level
    console = log_cfg.console if console is None else console

    log_dir = Path(log_cfg.directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
            '%(asctime)s [%(levelname)-7s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    file_handler = RotatingFileHandler(
            log_dir / log_cfg.file,
            maxBytes=log_cfg.max_bytes,
            backupCount=log_cfg.backup_count,
            encoding='utf-8',
        )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    
    if console:
        console_handler = _TqdmHandler()
        console_handler.setFormatter(fmt)
        root.addHandler(console_handler)

    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
