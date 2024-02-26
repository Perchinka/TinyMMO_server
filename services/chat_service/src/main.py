from src.config import Config
from confluent_kafka import Producer, Consumer
from pydantic import BaseModel
from datetime import datetime
import socket

class ChatMsg(BaseModel):
    content: str
    reciever: str
    timestamp: str


class KafkaAdapter:
    def __init__(self, config: Config):
        self.producer = Producer({
            'bootstrap.servers': config.KAFKA_URL,
            'client.id': socket.gethostname()
        })
        self.consumer = Consumer({
            'bootstrap.servers': config.KAFKA_URL,
            'group.id': 'chat_service',
        })
    
    def publish_msg(self, msg: ChatMsg):
        self.producer.produce('snd', key=msg.reciever, value=msg.content)
    

    
    
def main():
    config = Config()
    kafka = KafkaAdapter(config)
    chat_msg = ChatMsg(content='Hello', reciever='user1', timestamp=datetime.now().isoformat())
    kafka.publish_msg(chat_msg)
    kafka.producer.flush()

if __name__ == '__main__':
    main()