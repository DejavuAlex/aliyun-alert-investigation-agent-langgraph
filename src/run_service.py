import asyncio
import logging
import os
import sys

import uvicorn
from dotenv import load_dotenv

from env_config import set_env
from log_config import get_logger

set_env()
logger = get_logger(__name__,logging.DEBUG)
if __name__ == "__main__":
    # root_logger = logging.getLogger()
    # if root_logger.handlers:
    #     print(
    #         f"Warning: Root logger already has {len(root_logger.handlers)} handler(s) configured. "
    #         f"basicConfig() will be ignored. Current level: {logging.getLevelName(root_logger.level)}"
    #     )
    #
    # logging.basicConfig(level=settings.LOG_LEVEL.to_logging_level())
    uvicorn.run(
        "service.service:app",
        host="0.0.0.0",
        port=9000,
        reload= True if os.getenv("APP_ENV", "dev") == "dev" else False,
        timeout_graceful_shutdown=os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", 30),
    )
