import logging
import os

def get_logger(file_name: str) -> logging.Logger:
    print(f"for {file_name},get the logger level is {os.getenv('LOG_LEVEL','INFO')}")
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    logger = logging.getLogger(file_name)
    return logger
