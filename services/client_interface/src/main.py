from src.config import Config
from confluent_kafka import Producer, Consumer
from pydantic import BaseModel
import socket
import logging

from src.packets import ChatPacket

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
        self.producer.produce('rcv', key=str(msg.to_id), value="{} ; {}".format(msg.from_id, msg.content).encode('utf-8'))
        logging.info('Message published: {}'.format(msg))
    
    def consume_msg(self) -> ChatPacket:
        self.consumer.subscribe(['snd'])
        msg = self.consumer.poll(1.0)
        if msg is None:
            return None
        if msg.error():
            logging.error('Consumer error: {}'.format(msg.error()))
            return None
            
        to_id = int(msg.key().decode('utf-8'))
        from_id, content = msg.value().decode('utf-8').split(';', 1)
        return ChatPacket(to_id, from_id, content)

    

class Worker:
    def __init__(self, config: Config):
        self.config = config
        self.kafka = KafkaAdapter(config)
    
    def run(self):
        while True:
            packet = self.kafka.consume_msg()
            if packet is not None:
                logging.info('Sending {}'.format(packet))
            else:
                continue
    
    def listen(self):
        while True:
            to_id = int(input('To: '))
            from_id = int(input('From: '))
            content = input('Content: ')
            self.kafka.publish_msg(ChatMsg(to_id=to_id, from_id=from_id, content=content))