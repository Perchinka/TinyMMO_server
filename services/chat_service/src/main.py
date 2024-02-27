from src.config import Config
from confluent_kafka import Producer, Consumer
from pydantic import BaseModel
import socket
import logging


class ChatMsg(BaseModel):
    to_id: int
    from_id: int
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
        self.producer.produce('snd', key=str(msg.to_id), value="{} ; {}".format(msg.from_id, msg.content).encode('utf-8'))
        logging.info('Message published: {}'.format(msg))
    
    def consume_msg(self) -> ChatMsg:
        self.consumer.subscribe(['rcv'])
        raw_msg = self.consumer.poll()
        if raw_msg is None:
            return None
        if raw_msg.error():
            logging.error('Consumer error: {}'.format(raw_msg.error()))
            return None

        try:
            to_id = int(raw_msg.key())
            value = raw_msg.value().decode('utf-8')
            from_id = int(value.split(' ; ')[0])
            content = value.split(' ; ')[1]
            msg = ChatMsg(from_id=from_id, to_id=to_id, content=content)
        except Exception as e:
            logging.error('Error parsing message: {}'.format(e))
            return None
        
        logging.info('Consumer received new message: {}'.format(raw_msg))
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
            self.process_msg(msg)
    
    def process_msg(self, msg: ChatMsg):
        self.send_msg(msg)


def main():
    config = Config()
    chat_service = ChatService(config)
    chat_service.start_polling()

if __name__ == '__main__':
    main()