from datetime import datetime
import pytz
from loguru import logger
import sys

vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")

logger.remove()

logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

def patch_record(record):
    record["time"] = record["time"].astimezone(vietnam_tz)
    return True

logger = logger.patch(patch_record)


def get_date_time():
    return datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
