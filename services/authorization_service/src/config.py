import os
from src import logger

class Config:
    LOGGING_LEVEL: str

    DATABASE_URL: str
    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str

    def __init__(self):
        self.LOGGING_LEVEL = os.environ.get('LOGING_LEVEL')

        self.DATABASE_URL = os.environ.get('DATABASE_URL')
        self.DATABASE_USERNAME = os.environ.get('DATABASE_USERNAME')
        self.DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')

        logger.setup_logger(self.LOGGING_LEVEL)