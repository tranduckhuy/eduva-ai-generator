from datetime import datetime
import pytz
from loguru import logger
import sys

# Cấu hình logger để sử dụng múi giờ Việt Nam
vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")

# Xóa handler mặc định của loguru
logger.remove()

# Thêm handler mới với format thời gian theo múi giờ Việt Nam
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Cấu hình để chuyển đổi múi giờ cho tất cả log records
def patch_record(record):
    record["time"] = record["time"].astimezone(vietnam_tz)
    return True

logger = logger.patch(patch_record)


def get_date_time():
    return datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
