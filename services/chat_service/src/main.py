from src.config import Config
from confluent_kafka import Producer, Consumer
from pydantic import BaseModel
import socket
import logging


class ChatMsg(BaseModel):
    chanel_id: int
    content: str


class KafkaAdapter:
    def __init__(self, config: Config):
        self.producer = Producer({
            'bootstrap.servers': config.KAFKA_URL,
            'client.id': socket.gethostname()
        })
        self.consumer = Consumer({
            'bootstrap.servers': config.KAFKA_URL,
            'group.id': 'chat-service',
        })
    
    def publish_msg(self, msg: ChatMsg):
        self.producer.produce('snd', key=str(msg.chanel_id), value=msg.content)
        logging.info('Message published: {}'.format(msg))
    
    def consume_msg(self):
        self.consumer.subscribe(['rcv'])
        while True:
            raw_msg = self.consumer.poll(1.0)
            if raw_msg is None:
                continue
            if raw_msg.error():
                logging.error('Consumer error: {}'.format(raw_msg.error()))
                continue

            msg = ChatMsg(chanel_id=int(raw_msg.key().decode('utf-8')), content=raw_msg.value().decode('utf-8'))
            logging.info('Received message: {}'.format(msg))
            self.consumer.commit
    

def main():
    config = Config()
    kafka = KafkaAdapter(config)
    chat_msg = ChatMsg(chanel_id=1, content='Hello')
    kafka.publish_msg(chat_msg)
    kafka.producer.flush()
    kafka.consume_msg()

if __name__ == '__main__':
    main()