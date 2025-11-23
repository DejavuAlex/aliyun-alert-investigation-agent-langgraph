import logging
import os

import uvicorn

from env_config import set_env
from log_config import get_logger, setup_uvicorn_logging


logger = get_logger(__name__,logging.DEBUG)
if __name__ == "__main__":
    set_env()
    uvicorn_logger = setup_uvicorn_logging()
    uvicorn_logger.info("Uvicorn logging setup completed")
    uvicorn.run(
        "service.service:app",
        host="0.0.0.0",
        port=9000,
        reload= True if os.getenv("APP_ENV", "dev") == "dev" else False,
        timeout_graceful_shutdown=int(os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", 30)),
        log_config=None,
        access_log=True,
    )
