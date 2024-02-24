import os
from src import logger

class Config:
    LOGGING_LEVEL: str

    def __init__(self):
        self.LOGGING_LEVEL = os.environ.get('LOGING_LEVEL')

        logger.setup_logger(self.LOGGING_LEVEL)