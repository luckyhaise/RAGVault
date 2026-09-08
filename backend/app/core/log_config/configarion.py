import json
import logging
import logging.config

# from uvicorn import loggings
import sys
from pathlib import Path

file_path = Path(__file__).with_name("config.json")


def load_config():
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def configure_logging():
    try:
        config_data = load_config()
        logging.config.dictConfig(config_data)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        logging.basicConfig(
            level="INFO",
            stream=sys.stdout,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%a %S:%M:%H  %d-%m-%Y ",
        )
        logging.getLogger(__name__).exception(
            "Failed to load logging config; defaulted to basicConfig: %s",
            exc,
        )
