import logging
import re

LOGLEVEL = logging.DEBUG
MAX_ENTITY_COUNT = 100

# Constants
ENTITY_ID_PATTERN = re.compile(r"^[QLPE]\d+$")
TIMESTAMP_PATTERN = re.compile(r"^\d{14}$")
