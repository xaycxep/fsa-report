#conftest.py
import os
from pathlib import Path

os.environ.setdefault(
        'FGIS_CONFIG',
        str(Path(__file__).parent / 'test_config.yml'),
    )
