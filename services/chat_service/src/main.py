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
        raw_msg = self.consumer.poll()
        if raw_msg is None:
            return None
        if raw_msg.error():
            logging.error('Consumer error: {}'.format(raw_msg.error()))
            return None

        msg = ChatMsg(chanel_id=int(raw_msg.key().decode('utf-8')), content=raw_msg.value().decode('utf-8'))
        logging.info('Consumer received new message: {}'.format(msg))
        self.consumer.commit
        return msg
    

class ChatService:
    def __init__(self, config: Config):
        self.kafka = KafkaAdapter(config)
    
    def send_msg(self, msg: ChatMsg):
        self.kafka.publish_msg(msg)
        self.kafka.producer.flush()
    
    def start_polling(self): 
        while True:
            msg = self.kafka.consume_msg()
            if msg is None:
                continue
            # TODO Add chanel_id processing and sending message to the proper chat
            self.send_msg(msg)


def main():
    config = Config()
    chat_service = ChatService(config)
    chat_service.start_polling()

if __name__ == '__main__':
    main()