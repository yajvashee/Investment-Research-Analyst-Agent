"""Small shared logging setup used while the project is being built."""

import logging


def configure_logging() -> None:
    """Configure a simple, readable console logger once."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
