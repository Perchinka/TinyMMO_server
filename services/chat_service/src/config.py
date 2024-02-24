import os
from src import logger

class Config:
    LOGGING_LEVEL: str
    
    KAFKA_URL: str
    KAFKA_USERNAME: str
    KAFKA_PASSWORD: str

    def __init__(self):
        self.KAFKA_URL = os.environ.get('KAFKA_URL')
        self.KAFKA_USERNAME = os.environ.get('KAFKA_USERNAME')
        self.KAFKA_PASSWORD = os.environ.get('KAFKA_PASSWORD')

        self.LOGGING_LEVEL = os.environ.get('LOGING_LEVEL')

        logger.setup_logger(self.LOGGING_LEVEL)