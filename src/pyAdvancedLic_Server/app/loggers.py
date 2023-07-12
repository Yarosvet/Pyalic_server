from aiologger import Logger
from aiologger.handlers.files import AsyncTimedRotatingFileHandler, RolloverInterval
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.levels import LogLevel
from aiologger.formatters.base import Formatter
import sys

from .config import LOG_FILE

logger = None


if logger is None:
    logger = Logger(name="license_server", level=LogLevel.INFO)
    formatter = Formatter(
        "[%(filename)s:%(lineno)d (%(funcName)s)] %(asctime)s %(levelname)s \t %(message)s")
    file_handler = AsyncTimedRotatingFileHandler(LOG_FILE, when=RolloverInterval.DAYS, interval=1, utc=True,
                                                 backup_count=3)
    file_handler.formatter = formatter
    logger.add_handler(file_handler)
    stream_handler = AsyncStreamHandler(sys.stderr, level=LogLevel.INFO, formatter=formatter)
    logger.add_handler(stream_handler)
