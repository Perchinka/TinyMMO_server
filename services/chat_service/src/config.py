import os
from src import logger

class Config:
    LOGGING_LEVEL: str
    KAFKA_URL: str
    
    def __init__(self):
        self.KAFKA_URL = os.environ.get('KAFKA_URL')

        self.LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'DEBUG')

        logger.setup_logger(self.LOGGING_LEVEL)