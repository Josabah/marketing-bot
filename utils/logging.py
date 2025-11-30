import logging
import sys
from typing import Optional

def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )

    # Suppress noisy logs from libraries
    logging.getLogger('aiosqlite').setLevel(logging.WARNING)
    logging.getLogger('aiogram').setLevel(logging.WARNING)
