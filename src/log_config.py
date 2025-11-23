

import logging
import os
from logging.handlers import RotatingFileHandler
import sys

from env_config import set_env
set_env()

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

def get_logger(name: str = __name__, level: int = os.getenv("LOG_LEVEL","INFO")) -> logging.Logger:
    print("for file {}, set log level to: {}".format(name, level))
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    # file_handler = RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    # file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    # logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def setup_uvicorn_logging():
    """为 Uvicorn 设置日志"""
    # Uvicorn 使用的 logger 名称
    uvicorn_loggers = ["uvicorn", "uvicorn.error", "uvicorn.access"]

    for logger_name in uvicorn_loggers:
        get_logger(logger_name)

    return get_logger("uvicorn")