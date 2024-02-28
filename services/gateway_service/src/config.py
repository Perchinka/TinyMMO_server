import os
from src import logger

class Config:
    LOGGING_LEVEL: str
    KAFKA_URL: str
    LISTENER_HOST: str
    LISTENER_PORT: int

    def __init__(self):
        self.LOGGING_LEVEL = os.environ.get('LOGING_LEVEL', 'DEBUG')
        self.KAFKA_URL = os.environ.get('KAFKA_URL')
        self.LISTENER_HOST = os.environ.get('LISTENER_HOST', '0.0.0.0')
        self.LISTENER_PORT = int(os.environ.get('LISTENER_PORT', '51234'))

        logger.setup_logger(self.LOGGING_LEVEL)